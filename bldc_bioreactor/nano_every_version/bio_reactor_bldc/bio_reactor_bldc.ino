//Controll Manual:
//Math:

//Velocity = 
#include <avr/io.h>
#include <avr/cpufunc.h>
#include <avr/interrupt.h>


//define dummi Pins, can be updated via Serial
int en1 = 0;
int en2 = 1;
int en3 = 2;
int in1 = 3;
int in2 = 4;
int in3 = 5;

//Defines state of the diffrent Phases each param either High or Low: 1,0 
struct Phase{
  int en1Val;
  int en2Val;
  int en3Val;
  int in1Val;
  int in2Val;
  int in3Val;
};

//initializes the Phases 
struct Phase initPhase(int en1Val, int en2Val, int en3Val, int in1Val, int in2Val, int in3Val){
  struct Phase phase;

  phase.en1Val = en1Val;
  phase.en2Val = en2Val;
  phase.en3Val = en3Val;
  phase.in1Val = in1Val;
  phase.in2Val = in2Val;
  phase.in3Val = in3Val;

  return phase;
}
//Declare the 6 diffrent Phases 
struct Phase phase1;
struct Phase phase2;
struct Phase phase3;
struct Phase phase4;
struct Phase phase5;
struct Phase phase6;

//array of 6 which containis the diffrent Phases to loop thru 
struct Phase phaseArr[6];


float MS_TO_MIN = 1.0/60000.0;
int MIN_TO_MS = 60000;
float DEGREES_PER_PHASE = (10.0/360);
unsigned int MAX_COUNTER = 65535;

int phaseCounter = 0;

//runtime changebile controll variables
//in rpm
float maxVelocity = 0;
//in rpm^2
float acceleration = 0;
//in rpm
float currVelocity = 0;

//variable to set the counter on onboard timer(TBC0) proportional to the timeout
unsigned int counter = 0;

//prescaler to differ the range and acuracy of timeout
short int prescaler = 64;

// Current Count of prescale, manged in this program, not in 
int prescaleCount = 0;

//flag to controll if motor change velocity
bool doAccelerate = false;

//flag to controll either deceleration or acceleration
bool deceleration = false;

bool doRun = false;
bool debugMode = false;

//flag to set start program loop, set via Serial
bool setupDone = false;
unsigned long lastTime = millis();



void setup() {
  Serial.begin(9600);
  delay(500);

  //initialize the 6 diffrent phase states
  phase1 = initPhase(0,1,1,0,1,0);
  phase2 = initPhase(1,1,1,1,0,0);
  phase3 = initPhase(1,1,0,1,0,0);
  phase4 = initPhase(1,1,1,0,0,1);
  phase5 = initPhase(1,0,1,0,0,1);
  phase6 = initPhase(1,1,1,0,1,0);

  //array of 6 which contains all phase states, to loop thru  
  phaseArr[0] = phase1;
  phaseArr[1] = phase2;
  phaseArr[2] = phase3;
  phaseArr[3] = phase4;
  phaseArr[4] = phase5;
  phaseArr[5] = phase6;

  //loop to set the setup via Serial 
  while (setupDone == false){
    static String inputBuffer = "";
    while (Serial.available()) {
      char c = Serial.read();
      if (c == '\n') {
        inputBuffer.trim();
        if (inputBuffer.length() > 0) {
          parseAndHandle(inputBuffer);
        }
        inputBuffer = "";
      } else {
        inputBuffer += c;
    }
  }
  delay(500);
  }

  Serial.println("do setup timer");
  setupTimer();
  lastTime = millis();
}

void loop() {
  if (doRun){
    //if the current velocity of the bldc is smaler than the set max velocity
    //and if the acceleration variable is set to greater than 0, the Acceleration flag is set  
    if (currVelocity != maxVelocity && acceleration > 0.0){
      Serial.println("acceleration");
      doAccelerate = true;
    }
    //if acceleration flag is set the current velocity is updatet via acceleration param over the time since last update 
    if (doAccelerate){
      updateVelocity(millis() - lastTime);
      lastTime = millis();
      Serial.println("do accelerate");

    //if the acceleration flag is not set, the current velocity of the bldc is set to the max set velocity, can be controlled via Serial 
    }else{
      currVelocity = maxVelocity;
    }
    //calculates the counter to set the wanted timeout
    calculateCounter();
    //sets the counter on onbaord timer
    setCounter(counter);
  }

  //loop to check and handle Serial input
  static String inputBuffer = "";
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      inputBuffer.trim();
      if (inputBuffer.length() > 0) {
        parseAndHandle(inputBuffer);
      }
      inputBuffer = "";
    } else {
      inputBuffer += c;
    }
  }

  delay(200);

}
//updates the Pin out to controll the phases, gets an array of 6 integers.
void setupPin(int* pinArr){
  pinMode (en1, INPUT);
  pinMode (en2, INPUT);
  pinMode (en3, INPUT);
  pinMode (in1, INPUT);
  pinMode (in2, INPUT);
  pinMode (in3, INPUT);

  en1 = pinArr[0];
  in1 = pinArr[1];
  en2 = pinArr[2];
  in2 = pinArr[3];
  en3 = pinArr[4];
  in3 = pinArr[5];

  pinMode (en1, OUTPUT);
  pinMode (en2, OUTPUT);
  pinMode (en3, OUTPUT);
  pinMode (in1, OUTPUT);
  pinMode (in2, OUTPUT);
  pinMode (in3, OUTPUT);
}

//Setup onboard TCB0 timer
void setupTimer() {
  Serial.println("setupTimer");

  delay(500);

  Serial.println("1");

  //set TCB0 in Periodic Interrupt Mode
  TCB0.CTRLB = TCB_CNTMODE_INT_gc;

  TCB0.CCMP = 50000;

  //Enable Timer Interrupt
  TCB0.INTCTRL = TCB_CAPT_bm;

  //Start Timer
  TCB0.CTRLA = TCB_CLKSEL_CLKDIV1_gc | TCB_ENABLE_bm; // No prescaler, prescale is handeld in this program

  sei();  // activate Global interupts

  delay(500);
  Serial.println("setupTimer done");
}

// Internal Service Routine gets executed when Internal flag is set. 
ISR(TCB0_INT_vect){
  TCB0.INTFLAGS = TCB_CAPT_bm;
  if (doRun == true){
    //reset flag
    prescaleCount += 1;
    if (prescaleCount == prescaler){
      setPhase();
      prescaleCount = 0;
    }
  }
}

void setCounter(unsigned int inp_counter){
  Serial.print("set counter: ");
  Serial.println(inp_counter);
  TCB0.CCMP = inp_counter;
}

void calculateCounter(){
  float timeout_s = (DEGREES_PER_PHASE / currVelocity) * 60 ;
  unsigned long newCounter = (unsigned long)(timeout_s * F_CPU / prescaler);

  //the timeout can only be set in a range, given by the Prescale, since the counter variable on the oboard timer overfloats after 16bit 
  if (timeout_s > calculateMaxTimeout()){
    counter = 65535;
  }else if (timeout_s < calculateMinTimeout()){
    counter = 1;
  }else{
    counter = newCounter;
  }
}
 
void setPhase(){
  Phase phase = phaseArr[phaseCounter];
  phaseCounter = (phaseCounter + 1) % 6;

  digitalWrite(en1, phase.en1Val);
  digitalWrite(en2, phase.en2Val);
  digitalWrite(en3, phase.en3Val);
  digitalWrite(in1, phase.in1Val);
  digitalWrite(in2, phase.in2Val);
  digitalWrite(in3, phase.in3Val);
}

//gets a timeinterval timeDelta, since the last velocity change and either decreces or encreces the new current Velocity by checking if the
//maxVelocity is either smaller or bigger than the current Velocity, by the deceleration flag (is set after updating the new maxVelocity via Serial) 
void updateVelocity(float timeDelta){
  float timeDeltaMin = timeDelta * MS_TO_MIN;
  float velocityChange = timeDeltaMin * acceleration;
  bool limReached;
  float newVelocity;

  if (!deceleration){
    newVelocity = velocityChange + currVelocity;
    limReached = newVelocity > maxVelocity;
  }
  else{
    newVelocity = fabs(velocityChange - currVelocity);
    limReached = newVelocity < maxVelocity;
  }

  if (limReached){
    doAccelerate = false;
    currVelocity = maxVelocity;
  }
  else{
    currVelocity = newVelocity;
  }
}

void parseAndHandle(String input){
  String command;
  String valueStr;
  int delimiterIndex = input.indexOf(':');

  if (delimiterIndex != -1){
    command = input.substring(0, delimiterIndex);
    valueStr = input.substring(delimiterIndex + 1);
  } else {
    command = input;
  }

  handleCommand(command, valueStr);
}

// executes the given command
void handleCommand(String cmd, String value) {
  if (cmd == "status"){
    writeStatus();
  }
  else if (cmd == "setVelocity"){
    setVelocity(value.toFloat());
  }
  else if (cmd =="setAcceleration"){
    setAcceleration(value.toFloat());
  }
  else if (cmd == "runMotor"){
    setRun(value);
  }
  else if (cmd == "setupPin"){
    int pinArr[6];
    parsePinInput(pinArr, value);
    setupPin(pinArr);
    Serial.print("DONE");
  }
  else if(cmd == "setPrescale"){
    setPrescale(value.toInt());
  }
  else if (cmd == "setupDone"){
    setSetupDone(value.toInt());
  }
  else{
    Serial.print("invalid command: ");
  }
  Serial.println("sended: " + cmd + ":" + value);
}

//if the pinout is changed via Serial the String of 6 numbers, seperated by a coma, are parsed through and writen into the refrence array  
void parsePinInput(int* pinArr, String valueStr) {
  int lastIndex = 0;
  int currentIndex = 0;

  for (int i = 0; i < 6; i++) {
    currentIndex = valueStr.indexOf(',', lastIndex);
    
    if (currentIndex == -1) {
      pinArr[i] = valueStr.substring(lastIndex).toInt();
    } else {
      pinArr[i] = valueStr.substring(lastIndex, currentIndex).toInt();
      lastIndex = currentIndex + 1;
    }
  }
}

void writeStatus(){
  Serial.println("write status");
}

void writeInfo(){
Serial.print("FCPU:");
Serial.print(F_CPU);
Serial.print(", MaxCounter:");
Serial.print(MAX_COUNTER);
}

void setRun(String value){
  if (value == "1"){
    doRun = true;
    //reset Flag
  }
  else{
    doRun = false;
  }
}

float calculateMaxTimeout(){
  float maxTimeout = (float)MAX_COUNTER * prescaler / F_CPU;
  Serial.print("max possible timeout: ");
  Serial.println(maxTimeout);
  return maxTimeout;
}

float calculateMinTimeout(){
  float minTimeout = 1.0 * prescaler / F_CPU;
  Serial.print("min possible timeout: ");
  Serial.println(minTimeout);
}

void setVelocity(float velocity){
  if (maxVelocity < velocity){
    deceleration = false;
  }else{
    deceleration = true;
  }
  maxVelocity = velocity;
}

void setAcceleration (float a){
  if (a > 0){
    doAccelerate = true;
  }else{
    doAccelerate = false;
  }
    acceleration = a;
}

void setPrescale(int p){
  prescaler = p;
}

void setSetupDone(bool b){
  setupDone = b;
 }