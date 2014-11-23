// matt pinner @mpinner
//
// intent control simple led sequences from i2c
//
// depends on adafruits neopixel lib: http://adafruit.com
// borrowed heavily from i2c exampl by Nicholas Zambetti <http://www.zambetti.com>

// This example code is in the public domain.



// i2c lib 
// Teensy 2 requires 
//      - pin 5 = SCL  
//      - pin 6 = SDA 
#include <Wire.h>

// led driving code
#include <Adafruit_NeoPixel.h>

// configuration
#define NEOPIXEL_LEFT_PIN 12
#define NEOPIXEL_RIGHT_PIN 16

#define LED_COUNT 10
#define LED_BARS 2

// Constants defining communication protocol with teensy from Edison
#define OFF  0x00
#define COLOR 0x01
#define BRIGHTNESS 0x02
#define ANIMATION 0x03
#define COUNT 0x04
#define PROXIMITY 0x05
               
// Animation IDs which are arguments to 
#define PARK 0       
#define TERRITORIAL 1
#define POINT 2

// setup
Adafruit_NeoPixel leftStrip = Adafruit_NeoPixel(LED_COUNT, NEOPIXEL_RIGHT_PIN, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel rightStrip = Adafruit_NeoPixel(LED_COUNT, NEOPIXEL_LEFT_PIN, NEO_GRB + NEO_KHZ800);

// @deprecated : just for backward compatibility
Adafruit_NeoPixel strip = leftStrip;


int ledsPerBar = LED_COUNT / LED_BARS;

// Color Definitions
struct RGB {
  byte r;
  byte g;
  byte b;
};

int black = strip.Color(0, 0, 0);   // leds off
RGB current_color = {0, 0, 5};

RGB rgb_blue = {0, 0, 127};
RGB pure_white = {255, 255, 180};
RGB blue_in_between_state = {200, 200, 255};

int current_brightness = 200;
int current_animation_id = 0;

// controls how long animation plays
boolean shouldContinueAnimating = true;

void setup()
{

  // bring up i2c slave
  Wire.begin(4);                // join i2c bus with address #4
  Wire.onReceive(receiveEvent); // register event
  Serial.begin(9600);           // start serial for output

  // bring up led driver
  leftStrip.begin();
  rightStrip.begin();
  show(); // Initialize all pixels to 'off'

  // ???
  pinMode(0,OUTPUT);             // for verification

  paintLeds(12);

}


// doing nothing as we're handling this with software interupts at this time.
void loop()
{
  delay(50);
}

// function that executes whenever data is received from master
// this function is registered as an event, see setup()
void receiveEvent(int bytes)
{
  int cmd_id  = Wire.read();
  Serial.print("cmd: ");
  Serial.println(cmd_id);
  int num_bytes = Wire.available();
  Serial.print(num_bytes);
  Serial.println(" arguments available to read");

  int brigthtness;
  int id;
  
  switch (cmd_id) {
  case OFF:
    Serial.println("Turning Neopixel strip off");
    leds_off();
    break;
  case COLOR:
    Serial.println("Setting Neopixel strip color");
    set_color();
    break;
  case BRIGHTNESS:
    Serial.println("Setting Neopixel strip brightness");
    brigthtness = Wire.read();
    setBrightness(brigthtness);
    break;
  case COUNT:
    break;
  case ANIMATION:
    Serial.println("Setting Animation");
    id = Wire.read();
    set_animation(id);
    break;
  case PROXIMITY:
    Serial.println("Setting leds based on proximity data");
    set_proximity_leds();
    break;
  default:
    Serial.println(cmd_id);
    Serial.println("Cmd not matched!"); 
  }

  return;
}


// called to update leds
void paintLeds(int ledCount) { 

  for (int i = 0; i < ledsPerBar; i++) {
    for (int bar = 0; bar < LED_BARS; bar++) {

      int ledIndex = i+ledsPerBar*bar;

      if (ledCount > i) {
        // leds on
        setPixelColor(ledIndex, strip.Color(  0,   0, 127));
      } 
      else {
        // leds off
        setPixelColor(ledIndex, strip.Color(  0,   0, 12));
      }
    }
  }

  show();
}

void set_proximity_leds() {
  paintLeds(Wire.read());
}

void leds_off() {
  shouldContinueAnimating = false;  // stop previous animation
  // set all pixels to off
  for(int i=0;i<LED_COUNT;i++) {
    setPixelColor(i, black); 
    show();
  }

}

void set_color() { 
  current_color.r = Wire.read();
  current_color.g = Wire.read();
  current_color.b = Wire.read();
}

void set_animation(int id) {
  leds_off();  // stop previous animation
  current_animation_id = id;
  shouldContinueAnimating = true;  
  switch (id) {
  case PARK:
    animate_park();
    break;
  case TERRITORIAL:
    animate_territorial();
    break;
  case POINT:
    animate_point();
    break;
  default:
    Serial.print(id);
    Serial.println(" is unrecognized ID to animate!");
  }
}

void animate_park() {
  Serial.println("I'm park!!!");
  while (shouldContinueAnimating) {
    /*
    for(uint16_t i=0; i< LED_COUNT; i++) {
     int color = strip.Color(current_color.r, current_color.g, current_color.b);
     colorWipe(color, 50);
     }
     leds_off();
     delay(20);
     */
    heartbeat();
  }

}

void animate_point() {
  Serial.println("I'm point!!!");
  while (shouldContinueAnimating) {
    for(uint16_t i=0; i<LED_COUNT; i++) {
      Serial.println("inside loop");
      paintLeds(i);
      delay(50);
    }
  }
}

void animate_territorial() {
  Serial.println("I'm territorial!");
  while (shouldContinueAnimating) {
    colorWipe(strip.Color(255, 0, 0), 50); // Red
    colorWipe(strip.Color(0, 255, 0), 50); // Green
    colorWipe(strip.Color(0, 0, 255), 50); // Blue
  }
}

// Input a value 0 to 255 to get a color value.
// The colours are a transition r - g - b - back to r.
uint32_t Wheel(byte WheelPos) {
  WheelPos = 255 - WheelPos;
  if(WheelPos < 85) {
    return strip.Color(255 - WheelPos * 3, 0, WheelPos * 3);
  } 
  else if(WheelPos < 170) {
    WheelPos -= 85;
    return strip.Color(0, WheelPos * 3, 255 - WheelPos * 3);
  } 
  else {
    WheelPos -= 170;
    return strip.Color(WheelPos * 3, 255 - WheelPos * 3, 0);
  }
}

// Fill the dots one after the other with a color
void colorWipe(uint32_t c, uint8_t wait) {
  for(uint16_t i=0; i<LED_COUNT; i++) {
    setPixelColor(i, c);
    show();
    delay(wait);
  }
}

void heartbeat() {
  int greeno;
  int redo;
  int blueo;

  // all pixels show the same color:
  redo =random(255);
  greeno = random(255);
  blueo = random (255);
  setPixelColor(0, redo, greeno, blueo);
  setPixelColor(1, redo, greeno, blueo);
  setPixelColor(2, redo, greeno, blueo);

  show();
  delay (20);

  int x = 3;
  for (int ii = 1 ; ii <252 ; ii = ii = ii + x){
    setBrightness(ii);
    show();              
    delay(5);
  }

  x = 3;
  for (int ii = 252 ; ii > 3 ; ii = ii - x){
    setBrightness(ii);
    show();              
    delay(3);
  }
  delay(10);

  x = 6;
  for (int ii = 1 ; ii <255 ; ii = ii = ii + x){
    setBrightness(ii);
    show();              
    delay(2);  
  }
  x = 6;
  for (int ii = 255 ; ii > 1 ; ii = ii - x){
    setBrightness(ii);
    show();              
    delay(3);
  }
  delay (50); 
}


void show () {
  rightStrip.show();
  leftStrip.show();
  return;
}

void setBrightness (uint8_t brightness) {
  rightStrip.setBrightness(brightness);
  leftStrip.setBrightness(brightness);
  return;
}

void setPixelColor(uint16_t n, uint8_t r, uint8_t g, uint8_t b) {
  rightStrip.setPixelColor(n, r, g, b);
  leftStrip.setPixelColor(n, r, g, b);
  return;
}

void setPixelColor(uint16_t n, uint32_t c) {
  rightStrip.setPixelColor(n, c);
  leftStrip.setPixelColor(n, c);  
}



