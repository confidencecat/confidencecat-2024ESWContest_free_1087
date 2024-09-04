#include <Servo.h>

// 핀 설정
const int stepPin = 5;
const int dirPin = 2;
const int enPin = 8;
const int servoPin2 = 10;  // 두 번째 서보모터 핀

// 변수 초기화
int steps = 0;
bool direction = true;
Servo servo2;
int initialAngle1 = 180;  // 두 번째 서보모터 초기 각도

void setup() {
  // 스텝 모터 핀 초기화
  pinMode(stepPin, OUTPUT);
  pinMode(dirPin, OUTPUT);
  pinMode(enPin, OUTPUT);
  digitalWrite(enPin, LOW);

  // 두 번째 서보 모터 핀 초기화
  servo2.attach(servoPin2);
  servo2.write(initialAngle1);

  // 시리얼 통신 시작
  Serial.begin(9600);
  Serial.println("Arduino is ready");
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();

    // 스텝 모터 제어
    if (command == 'M') {
      steps = Serial.parseInt();
      if (steps < 0) {
        direction = false;
        steps = -steps;
      } else {
        direction = true;
      }

      digitalWrite(dirPin, direction ? HIGH : LOW);

      for (int x = 0; x < steps; x++) {
        digitalWrite(stepPin, HIGH);
        delayMicroseconds(800);  // 속도를 느리게 하기 위해 증가
        digitalWrite(stepPin, LOW);
        delayMicroseconds(800);  // 속도를 느리게 하기 위해 증가
      }

      Serial.print("Moved ");
      Serial.print(steps);
      Serial.println(" steps.");
    }

    // 두 번째 서보 모터 제어 (10번 핀)
    else if (command == 'O') {
      servo2.write(0); // 서보모터를 0도로 이동
      delay(500);         // 속도를 느리게 하기 위해 증가
 
      servo2.write(180);   // 서보모터를 180도로 이동
      delay(500);         // 속도를 느리게 하기 위해 증가

      Serial.println("Servo2 moved to 0 and 180 degrees");
    }

    // 두 번째 서보 모터를 초기 각도로 되돌리기 (S 명령)
    else if (command == 'S') {
      servo2.write(initialAngle1);  // 초기 각도로 이동
      Serial.println("Servo2 returned to initial angle");
    }
  }
}