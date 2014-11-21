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
#define NEOPIXEL_PIN 15
#define LED_COUNT 20
#define LED_BARS 2

// setup
Adafruit_NeoPixel strip = Adafruit_NeoPixel(48, NEOPIXEL_PIN, NEO_GRB + NEO_KHZ800);

int ledsPerBar = LED_COUNT / LED_BARS;

// Color Definitions
struct RGB {
  byte r;
  byte g;
  byte b;
};

int black = strip.Color(0, 0, 0); // off
RGB current_color = {0, 0, 5};
int current_animation_id = 1;

// controls how long animation plays
bool animate = false;

void setup()
{

  // bring up i2c slave
  Wire.begin(4);                // join i2c bus with address #4
  Wire.onReceive(receiveEvent); // register event
  Serial.begin(9600);           // start serial for output

  // bring up led driver
  strip.begin();
  strip.show(); // Initialize all pixels to 'off'

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
  
  switch (cmd_id) {
    case 0:
      Serial.println("Turning Neopixel strip off");
      leds_off();
      break;
    case 1:
      Serial.println("Setting Neopixel strip color");
      set_color();
      break;
    case 2:
      Serial.println("Setting Animation");
      set_animation();
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
        strip.setPixelColor(ledIndex, strip.Color(  0,   0, 127));
      } 
      else {
        // leds off
        strip.setPixelColor(ledIndex, strip.Color(  0,   0, 12));
      }
    }
  }

  strip.show();
}

void leds_off() {
   animate = false;
   for(int i=0;i<LED_COUNT;i++) {
    strip.setPixelColor(i, black); 
    strip.show();
   }
   
}

void set_color() { 
  current_color.r = Wire.read();
  current_color.g = Wire.read();
  current_color.b = Wire.read();
}

void set_animation() {
  animate = false;
  int id = Wire.read();
  switch (id) {
    case 0:
      animate_park();
      break;
    case 1:
      animate_territorial();
      break;
    case 2:
      animate_point();
      break;
    default:
      Serial.print(id);
      Serial.println(" is unrecognized ID to animate!");
  }
}

void animate_park() {
  Serial.println("I'm park!!!");
  animate = true;
  while (animate) {
    for(uint16_t i=0; i< LED_COUNT; i++) {
      int color = strip.Color(current_color.r, current_color.g, current_color.b);
      colorWipe(color, 50);
    }
    leds_off();
    delay(20);
  }

}

void animate_point() {
 Serial.println("I'm point!!!");
 animate = true;
 while (animate) {
   for(uint16_t i=0; i<LED_COUNT; i++) {
     Serial.println("inside loop");
     paintLeds(i);
     delay(50);
   }
 }
}

void animate_territorial() {
  Serial.println("I'm territorial!");
  animate = true;
  while (animate) {
    colorWipe(strip.Color(255, 0, 0), 50); // Red
    colorWipe(strip.Color(0, 255, 0), 50); // Green
    colorWipe(strip.Color(0, 0, 255), 50); // Blue
  }
  leds_off();
}

// Input a value 0 to 255 to get a color value.
// The colours are a transition r - g - b - back to r.
uint32_t Wheel(byte WheelPos) {
  WheelPos = 255 - WheelPos;
  if(WheelPos < 85) {
   return strip.Color(255 - WheelPos * 3, 0, WheelPos * 3);
  } else if(WheelPos < 170) {
    WheelPos -= 85;
   return strip.Color(0, WheelPos * 3, 255 - WheelPos * 3);
  } else {
   WheelPos -= 170;
   return strip.Color(WheelPos * 3, 255 - WheelPos * 3, 0);
  }
}

// Fill the dots one after the other with a color
void colorWipe(uint32_t c, uint8_t wait) {
  for(uint16_t i=0; i<LED_COUNT; i++) {
      strip.setPixelColor(i, c);
      strip.show();
      delay(wait);
  }
}


