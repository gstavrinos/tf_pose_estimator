#!/usr/bin/env python
import tf
import rospy
import traceback
from tf import TransformListener
from tf2_msgs.msg import TFMessage
from geometry_msgs.msg import PoseStamped
from tf_pose_estimator.msg import PosesAndVelocities
from tf_pose_estimator.msg import Velocity

tf_ = None
p_v_pub = None
targeted_tf = ''
sliding_window = []
sliding_window_v = []
sliding_window_sz = 0

def init():
    global targeted_tf, tf_, sliding_window_sz
    global p_v_pub
    rospy.init_node('tf_velocity_estimator')
    targeted_tf = rospy.get_param("~targeted_tf", "helipad")
    sliding_window_sz = rospy.get_param("~sliding_window_sz", 10)
    tf_ = TransformListener()
    rospy.Subscriber("tf", TFMessage, tf_callback)
    p_v_pub = rospy.Publisher("tf_velocity_estimator/poses_velocities", PosesAndVelocities, queue_size=1)
    while not rospy.is_shutdown():
        rospy.spin()

def tf_callback(tf2):
    global targeted_tf, tf_
    global sliding_window_sz, sliding_window, sliding_window_v
    global p_v_pub
    #if tf_.frameExists("odom") :#and tf_.frameExists(targeted_tf):
    try:
        t = tf_.getLatestCommonTime("/odom", targeted_tf)
        position, quaternion = tf_.lookupTransform("/odom", targeted_tf, t)
        # Untested from here
        ps = PoseStamped()
        ps.header.stamp = rospy.Time.now()
        ps.header.frame_id = targeted_tf
        ps.pose.position.x = position[0]
        ps.pose.position.y = position[1]
        ps.pose.position.z = position[2]
        ps.pose.orientation.x = quaternion[0]
        ps.pose.orientation.y = quaternion[1]
        ps.pose.orientation.z = quaternion[2]
        ps.pose.orientation.w = quaternion[3]
        sliding_window.append(ps)
        if len(sliding_window) >= sliding_window_sz:
            del sliding_window[0]
            if len(sliding_window_v) >= sliding_window_sz:
                del sliding_window_v[0]
        vx = 0
        vy = 0
        vz = 0
        v = [vx, vy, vz]
        latest_continuous = 0
        if len(sliding_window) > 1:
            dx = sliding_window[-1].pose.position.x - sliding_window[-2].pose.position.x
            dy = sliding_window[-1].pose.position.y - sliding_window[-2].pose.position.y
            dz = sliding_window[-1].pose.position.z - sliding_window[-2].pose.position.z
            dt = (sliding_window[-1].header.stamp.secs + sliding_window[-1].header.stamp.nsecs * 10e-9) - (sliding_window[-2].header.stamp.secs + sliding_window[-2].header.stamp.nsecs * 10e-9)
            vx = dx / dt
            vy = dy / dt
            vz = dz / dt
            v = Velocity()
            v.vx = vx
            v.vy = vy
            v.vz = vz
            sliding_window_v.append(v)
        else:
            sliding_window_v.append(v)
        # Till here!
    except Exception as e:
        print traceback.format_exc()

    pvmsg = PosesAndVelocities()
    pvmsg.latest_poses = sliding_window
    pvmsg.latest_velocities = sliding_window_v
    p_v_pub.publish(pvmsg)

if __name__ == '__main__':
    init() 