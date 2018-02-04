int value;
int previousvalue;

#define RED 0
#define SILVER 1
int currentstate=SILVER;

unsigned long nbRead=0;
unsigned long nbTurns=0;

#define HIGH_THRESHOLD 60
#define LOW_THRESHOLD  30

char message[30];

void setup() {
  Serial.begin(115200);
}

void sendMessage(char message[30]) {
  Serial.println(message);
}

void loop(){
  value = analogRead(A0)/4;
  nbRead++;
  
  // For debug / calibration
  //sprintf(message, "val:%d", value);
  //sendMessage(message);
  
  if ((currentstate == SILVER) && (value > HIGH_THRESHOLD) && (previousvalue > HIGH_THRESHOLD)) {
    currentstate = RED;
  }
  
  if((currentstate == RED) && (value < LOW_THRESHOLD) && (previousvalue < LOW_THRESHOLD))  {
    currentstate = SILVER;
    nbTurns++;
    sprintf(message, "water:top:%d", nbTurns);
    sendMessage(message);  
  } else if ((nbRead % 50) == 0) {
    sprintf(message, "water:alive");
    sendMessage(message); 
  }
  
  // Loop at 10 Hz
  previousvalue = value;
  delay(100);
}
