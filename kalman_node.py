#!/usr/bin/env python
import csv
#import matplotlib
import numpy as np
import gps_assisted_simulator_node 
import subprocess
from std_msgs.msg import Float32
#from matplotlib import pyplot as plt
import rospy
import kalman_real_time
import requestHandler
from std_msgs.msg import Int32MultiArray
from std_msgs.msg import Float32MultiArray
from std_msgs.msg import MultiArrayLayout
from std_msgs.msg import MultiArrayDimension



def bike_state(data):
    velocity = data.data[6]
    yaw = data.data[9]
    #rospy.loginfo("Velocity is %f", velocity)
    #rospy.loginfo("Yaw is %f", yaw)
    bike_yv = [yaw, velocity]
    
def gps(data):
    #Important fields from data
    latitude = data.data[0] # In degrees
    longitude = data.data[1]
    time_step = data.data[10]
    #psi = data.data[7] # psi = heading in radians
    #velocity = data.data[8]
    # Converts lat long to x,y 
    x, y = requestHandler.math_convert(float(latitude), float(longitude)) 
    # gps current state - only relevant fields
    #rospy.loginfo("x is %f", x)
    #rospy.loginfo("y is %f", y)
    #rospy.loginfo(rospy.is_shutdown())
    #rospy.loginfo("timestep is %f", time_step)
    gps_xy = [x, y]
   


def listener():
    pub = rospy.Publisher('kalman_pub', Float32MultiArray, queue_size=10)
    rospy.init_node('kalman', anonymous=True)
    rospy.Subscriber("bike_state", Float32MultiArray, bike_state)
    rospy.Subscriber("gps", Float32MultiArray, gps)
    #rospy.spin()  
    rate = rospy.Rate(100)
    #Run until the nodes are shutdown (end.sh run OR start.sh was killed)
    while not rospy.is_shutdown():
        dim = [MultiArrayDimension('data', 1, 4)]
        layout = MultiArrayLayout(dim, 0)
        # The Kalman filter wants the GPS data in matrix form
        #Build matrix from gps x,y coordinates and bike velocity and yaw
        gps_matrix = np.matrix(gps_xy + bike_yv + time_step)
        #rospy.loginfo(gps_matrix)
        #save gps state values for later plotting
        gps_data.append(gps_matrix)
        if len(gps_data) >= 1:
            C = np.matrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
            #If we have 
            if len(gps_data) == 1:
                P_initial = np.matrix([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
                x_pos = gps_matrix[:,0]
                y_pos = gps_matrix[:,1]
                yaw = gps_matrix[:,2]
                v = gps_matrix[:,3]
                v_0 = v.item(0)
                yaw_0 = yaw.item(0)
                x_dot_0 = v_0 * np.cos(yaw_0)
                y_dot_0 = v_0 * np.sin(yaw_0)
                s_initial = np.matrix([[x_pos.item(0)], [y_pos.item(0)], [x_dot_0], [y_dot_0]])
                #output matrix - returns a tuple - first entry - kalman state (x,y,x',y')
                #                             - second entry - prediction error (p)
                output_matrix = kalman_real_time.kalman_no_loop(gps_matrix, C, s_initial, P_initial)
            else:
                output_matrix = kalman_real_time.kalman_no_loop(gps_matrix, C, 
                                                     kalman_state_matrix, p_state_matrix) 
            #rospy.loginfo(output_matrix.shape)
            kalman_state_matrix = output_matrix[0] 
            p_state_matrix = output_matrix[1]                                           
            #Change output_matrix to a standard array for publishing
            kalman_state = output_matrix[0].flatten().tolist()[0]
            #rospy.loginfo(kalman_state)
            p_state = output_matrix[1].flatten()
            #save predicted state values for later plotting
            #kalman_data.append(kalman_state_matrix) 
            #pub.publish(layout, kalman_state)
        pub.publish(layout, kalman_state)
        rate.sleep()
        #rospy.loginfo('SUCCESSFUL ITERATION')
    #rospy.loginfo('Test was terminated')
    #rospy.spin()
    # Plot the GPS data
    #plt.scatter(gps_data[:,0], gps_data[:,1], c='r')
    # Plot the Kalman output
    #plt.scatter(kalman_data[:,0], kalman_data[:,1])
    # Show everything
    #plt.show()

if __name__ == '__main__':
    #Data from bike_state and gps respectively
    gps_xy = [0,0] #x,y converted from latitude and longitude from gps
    bike_yv = [0,0] #bike velocity and yaw
    time_step = [0]
    #kalman/gps data saved as we go for later plotting
    kalman_data = np.matrix([0])
    gps_data = []
    #state that is published to ROS
    kalman_state = []
    p_state = []
    #State used for kalman_no loop
    kalman_state_matrix = np.matrix([0])
    p_state_matrix = np.matrix([0])

    listener()
    
