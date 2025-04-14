#include <string.h>
#include <stdio.h>
#include <unistd.h>

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"
#include "esp_log.h"
#include "esp_system.h"

#include <uros_network_interfaces.h>
#include <rcl/rcl.h>
#include <rcl/error_handling.h>
#include <std_msgs/msg/int32.h> // Using Int32 for communication
#include <rclc/rclc.h>
#include <rclc/executor.h>

#ifdef CONFIG_MICRO_ROS_ESP_XRCE_DDS_MIDDLEWARE
#include <rmw_microros/rmw_microros.h>
#endif

#define RCCHECK(fn) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){printf("Failed status on line %d: %d. Aborting.\n",__LINE__,(int)temp_rc);vTaskDelete(NULL);}}
#define RCSOFTCHECK(fn) { rcl_ret_t temp_rc = fn; if((temp_rc != RCL_RET_OK)){printf("Failed status on line %d: %d. Continuing.\n",__LINE__,(int)temp_rc);}}

// --- GLOBALS ---
rcl_publisher_t wasd_status_publisher;
rcl_subscription_t wasd_cmd_subscriber;
std_msgs__msg__Int32 status_msg; // Stores the current desired status (0=Stop, 1=W, 2=A, 3=S, 4=D)
std_msgs__msg__Int32 cmd_msg;

// --- Timer Callback ---
// Publishes the current value of status_msg.data periodically
void status_publish_timer_callback(rcl_timer_t * timer, int64_t last_call_time)
{
	(void) last_call_time;
	if (timer != NULL) {
		// Try publishing the current status. Network issues might cause errors.
		RCSOFTCHECK(rcl_publish(&wasd_status_publisher, &status_msg, NULL));
		// Optional: Reduce print frequency if needed
        // static int count = 0;
        // if (++count % 5 == 0) { // Print every ~2.5 seconds
		//      printf("Current Status Sent: %d\n", (int)status_msg.data);
        // }
	}
}

// --- Subscription Callback ---
// Updates the global status_msg based on received command
void command_subscription_callback(const void * cmd_msgin)
{
	const std_msgs__msg__Int32 * msg = (const std_msgs__msg__Int32 *)cmd_msgin;
    if (msg == NULL) {
         printf("Callback: Received NULL command msg pointer\n");
         return;
    }

	int32_t received_cmd = msg->data;
	printf("Received Command: %d\n", (int)received_cmd);

    // --- Logic: Map 1,2,3,4,0 -> 1,2,3,4,0; Others -> 0 ---
    if (received_cmd == 1) {         // W
        status_msg.data = 1;
    } else if (received_cmd == 2) {  // A
        status_msg.data = 2;
    } else if (received_cmd == 3) {  // S
        status_msg.data = 3;
    } else if (received_cmd == 4) {  // D
        status_msg.data = 4;
    } else if (received_cmd == 0) {  // Spacebar (STOP)
        status_msg.data = 0;
    }
    // --- CHANGE: We don't need an else block if we want to ignore other invalid integers ---
    // --- OR map others to 0 if preferred:
    // else {
    //     status_msg.data = 0; // Map any other received number to STOP
    //     printf("Received invalid command (%d), setting status to 0 (STOP).\n", (int)received_cmd);
    // }
    printf("Internal Status set to: %d\n", (int)status_msg.data);
    // Publishing is handled by the timer callback
}

// --- micro_ros_task ---
void micro_ros_task(void * arg)
{
	rcl_allocator_t allocator = rcl_get_default_allocator();
	rclc_support_t support;

	rcl_init_options_t init_options = rcl_get_zero_initialized_init_options();
	RCCHECK(rcl_init_options_init(&init_options, allocator));
#ifdef CONFIG_MICRO_ROS_ESP_XRCE_DDS_MIDDLEWARE
	rmw_init_options_t* rmw_options = rcl_init_options_get_rmw_init_options(&init_options);
	RCCHECK(rmw_uros_options_set_udp_address(CONFIG_MICRO_ROS_AGENT_IP, CONFIG_MICRO_ROS_AGENT_PORT, rmw_options));
#endif
	RCCHECK(rclc_support_init_with_options(&support, 0, NULL, &init_options, &allocator));

	rcl_node_t node = rcl_get_zero_initialized_node();
	RCCHECK(rclc_node_init_default(&node, "esp32_wasd_node", "", &support));

	RCCHECK(rclc_publisher_init_default(
		&wasd_status_publisher, &node,	ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),	"wasd_status"));

	RCCHECK(rclc_subscription_init_default(
		&wasd_cmd_subscriber, &node, ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32), "wasd_command"));

	rcl_timer_t status_timer = rcl_get_zero_initialized_timer();
	const unsigned int timer_period_ms = 500; // Publish status every 500ms
	RCCHECK(rclc_timer_init_default(
		&status_timer, &support, RCL_MS_TO_NS(timer_period_ms), status_publish_timer_callback));

	rclc_executor_t executor = rclc_executor_get_zero_initialized_executor();
	RCCHECK(rclc_executor_init(&executor, &support.context, 2, &allocator)); // timer + subscriber = 2 handles

	RCCHECK(rclc_executor_add_timer(&executor, &status_timer));
	RCCHECK(rclc_executor_add_subscription(
        &executor, &wasd_cmd_subscriber, &cmd_msg, &command_subscription_callback, ON_NEW_DATA));

	status_msg.data = 0; // Default status is 0 (STOP)
    printf("ESP32 WASD Node started. Waiting for commands on /wasd_command...\n");
	while(1){
		rclc_executor_spin_some(&executor, RCL_MS_TO_NS(100));
		usleep(10000);
	}

	// --- Cleanup ---
    RCCHECK(rcl_timer_fini(&status_timer));
	RCCHECK(rcl_subscription_fini(&wasd_cmd_subscriber, &node));
	RCCHECK(rcl_publisher_fini(&wasd_status_publisher, &node));
	RCCHECK(rcl_node_fini(&node));
    RCCHECK(rclc_support_fini(&support));
    RCCHECK(rcl_init_options_fini(&init_options));
  	vTaskDelete(NULL);
}

// --- app_main remains the same ---
void app_main(void)
{
#if defined(CONFIG_MICRO_ROS_ESP_NETIF_WLAN) || defined(CONFIG_MICRO_ROS_ESP_NETIF_ENET)
    ESP_ERROR_CHECK(uros_network_interface_initialize());
#endif
    xTaskCreate(micro_ros_task, "uros_task", CONFIG_MICRO_ROS_APP_STACK, NULL, CONFIG_MICRO_ROS_APP_TASK_PRIO, NULL);
}