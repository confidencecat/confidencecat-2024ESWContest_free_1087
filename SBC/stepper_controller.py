#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import serial

class StepperController(Node):
    def __init__(self):
        super().__init__('stepper_controller')

        # 퍼블리셔 설정 (JointTrajectory)
        self.publisher_ = self.create_publisher(JointTrajectory, '/joint_trajectory_controller/joint_trajectory', 10)
        self.joint_name = "slider_to_cart"
        self.current_position = 0  # 초기 위치를 0으로 설정

        # 아두이노 시리얼 통신 설정
        self.serial_port = '/dev/ttyACM0'  # 아두이노 시리얼 포트 경로
        self.baud_rate = 9600  # 시리얼 통신 속도
        self.arduino = None
        self.connect_to_arduino()

        # 스텝 모터 이동 관련 설정
        self.steps_to_meters_factor = 0.0000075  # 스텝 당 이동 거리 (m/스텝)
        self.sync_factor = 10  # 슬라이드바와 URDF 모델 간의 비율
        self.max_steps = 20500  # 최대 스텝 수
        self.min_position = 0  # 최소 위치
        self.max_position = self.max_steps * self.steps_to_meters_factor * self.sync_factor
        self.step_size = 500  # 한 번에 이동할 스텝 크기
        self.direction = -1  # 초기 이동 방향 (전진: 음수)

        # 주기적으로 스텝 모터를 이동시키기 위한 타이머 설정
        self.timer = self.create_timer(1.0, self.move_motor)

    def connect_to_arduino(self):
        try:
            self.arduino = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            self.get_logger().info(f"Connected to Arduino on {self.serial_port} at {self.baud_rate} baud")
        except serial.SerialException as e:
            self.get_logger().error(f"Failed to connect to Arduino: {e}")

    def move_motor(self):
        # 새로운 위치를 계산
        new_position = self.current_position + (self.direction * self.step_size)

        # 범위를 벗어나면 방향 전환
        if new_position < self.min_position or new_position > self.max_steps:
            self.direction *= -1  # 방향을 반대로 전환
            new_position = self.current_position + (self.direction * self.step_size)

        # 위치를 업데이트하고 슬라이드바에 전송
        self.current_position = new_position
        self.send_trajectory_command(self.current_position * self.steps_to_meters_factor * self.sync_factor)

        # 아두이노로 명령 전송 (방향에 따라 부호를 반대로 처리)
        steps = -self.direction * self.step_size
        self.send_to_arduino(steps)

    def send_trajectory_command(self, position):
        traj_msg = JointTrajectory()
        traj_msg.joint_names = [self.joint_name]
        point = JointTrajectoryPoint()
        point.positions = [position]
        point.time_from_start.sec = 1
        traj_msg.points = [point]
        self.publisher_.publish(traj_msg)

    def send_to_arduino(self, steps):
        if self.arduino is not None:
            command = f"M {steps}\n"  # "M"과 스텝 수를 포함한 명령어 생성
            self.arduino.write(command.encode())  # 명령어를 아두이노로 전송
            self.get_logger().info(f'Sent to Arduino: "{command.strip()}"')
            
            # 아두이노의 응답 읽기 및 현재 위치 표시
            response = self.arduino.readline().decode().strip()
            self.get_logger().info(f'Arduino Response: {response}. Current Position: {self.current_position}/{self.max_steps} steps.')
        else:
            self.get_logger().error('Serial connection to Arduino not established.')

def main(args=None):
    rclpy.init(args=args)
    stepper_controller = StepperController()
    rclpy.spin(stepper_controller)
    stepper_controller.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()