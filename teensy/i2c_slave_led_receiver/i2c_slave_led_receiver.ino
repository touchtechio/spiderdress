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
#define GLOW 3
#define GLOW_SLOW 4

uint8_t LED_Breathe_Table[]  = {   80,  87,  95, 103, 112, 121, 131, 141, 151, 161, 172, 182, 192, 202, 211, 220,
              228, 236, 242, 247, 251, 254, 255, 255, 254, 251, 247, 242, 236, 228, 220, 211,
              202, 192, 182, 172, 161, 151, 141, 131, 121, 112, 103,  95,  87,  80,  73,  66,
               60,  55,  50,  45,  41,  38,  34,  31,  28,  26,  24,  22,  20,  20,  20,  20,
               20,  20,  20,  20,  20,  20,  20,  20,  20,  20,  20,  20,  20,  20,  20,  20,
               20,  20,  20,  20,  20,  20,  20,  20,  20,  20,  20,  20,  22,  24,  26,  28,
               31,  34,  38,  41,  45,  50,  55,  60,  66,  73 };


#define BREATHE_TABLE_SIZE (sizeof(LED_Breathe_Table))
#define BREATHE_CYCLE    6000      /*breathe cycle in milliseconds*/
#define BREATHE_UPDATE    (BREATHE_CYCLE / BREATHE_TABLE_SIZE)

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

int current_led_count = LED_COUNT;

int black = strip.Color(0, 0, 0);   // leds off
RGB current_color = {0, 0, 127};

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
  int animation_id;
  int current_led_count;
  
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
    Serial.println("Setting Neopixel strip led count");
    current_led_count = Wire.read();
    Serial.println(current_led_count);
    break;
  case ANIMATION:
    Serial.println("Setting Animation");
    leds_off();
    animation_id = Wire.read();
    set_animation(animation_id);
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
        setPixelColor(ledIndex, strip.Color(  current_color.r, current_color.g, current_color.b));
      } 
      else {
        // leds off
        setPixelColor(ledIndex, strip.Color( current_color.r, current_color.g, current_color.b / 7 ));
      }
    }
  }

  show();
}

void set_proximity_leds() {
  paintLeds(Wire.read());
}

void leds_off() {
  Serial.print("Led count is: ");
  Serial.println(current_led_count);
  
  shouldContinueAnimating = false;  // stop previous animation
  // set all pixels to off
  for(int i=0;i<current_led_count;i++) {
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
  int glow_type;
  int glow_speed;
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
  case GLOW:
    glow_type = 0;
    glow_speed = 6000;
    animate_glow(glow_type, glow_speed);
    break;
  case GLOW_SLOW:
    glow_type = 0;
    glow_speed = 1000;
  default:
    Serial.print(id);
    Serial.println(" is unrecognized ID to animate!");
  }
}

void animate_park() {
  Serial.println("I'm park!!!");
  while (shouldContinueAnimating) {
    for(uint16_t i=0; i< current_led_count; i++) {
       if (shouldContinueAnimating) {
         int color = strip.Color(current_color.r, current_color.g, current_color.b);
         colorWipe(color, 50);
       } else {
         break;
       }
     }
     delay(20);
  }

}

void animate_point() {
  Serial.println("I'm point!!!");
  while (shouldContinueAnimating) {
    for(uint16_t i=0; i<current_led_count; i++) {
      if (shouldContinueAnimating) {
        paintLeds(i);
        delay(50);
      } else {
        break;
      }
    }
  }
}

void animate_territorial() {
  Serial.println("I'm territorial!");
  while (shouldContinueAnimating) {
    colorWipe(strip.Color(current_color.r, current_color.g, current_color.b), 50);
  }
}

void animate_glow(int type, int rate) {
  int cycle;
  int breath_update = rate / sizeof(LED_Breathe_Table);
  
  while (shouldContinueAnimating) {
    for (cycle=0; cycle < 4; cycle++) {
        if (type == 0)
          uniformBreathe(LED_Breathe_Table, BREATHE_TABLE_SIZE, breath_update, current_color.r, current_color.g, current_color.b);
        else
          sequencedBreathe(LED_Breathe_Table, BREATHE_TABLE_SIZE, breath_update, current_color.r, current_color.g, current_color.b);
      }
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
  for(uint16_t i=0; i<current_led_count; i++) {
    if (shouldContinueAnimating) {
      setPixelColor(i, c);
      show();
      delay(wait);
    } else {
      break;
    }
  }
}

void uniformBreathe(uint8_t* breatheTable, uint8_t breatheTableSize, uint16_t updatePeriod, uint16_t r, uint16_t g, uint16_t b)
{
  int i;
  uint8_t breatheIndex = 0;
  uint8_t breatheRed;
  uint8_t breatheGrn;
  uint8_t breatheBlu;
  
  for (breatheIndex = 0; breatheIndex < breatheTableSize; breatheIndex++) {
    for (i=0; i < current_led_count; i++) {
      breatheRed = (r * breatheTable[breatheIndex]) / 256;
      breatheGrn = (g * breatheTable[breatheIndex]) / 256;
      breatheBlu = (b * breatheTable[breatheIndex]) / 256;
      strip.setPixelColor(i, breatheRed, breatheGrn, breatheBlu);
    }
    strip.show();   // write all the pixels out
    delay(updatePeriod);
  }
}

void sequencedBreathe(uint8_t* breatheTable, uint8_t breatheTableSize, uint16_t updatePeriod, uint16_t r, uint16_t g, uint16_t b)
{
  int i;
  uint8_t breatheIndex = 0;
  uint8_t breatheRed;
  uint8_t breatheGrn;
  uint8_t breatheBlu;
  uint8_t sequenceIndex;
  
  for (breatheIndex = 0; breatheIndex < breatheTableSize; breatheIndex++) {
    for (i=0; i < current_led_count; i++) {
      sequenceIndex = (breatheIndex + (i*4)) % breatheTableSize;
      breatheRed = (r * breatheTable[sequenceIndex]) / 256;
      breatheGrn = (g * breatheTable[sequenceIndex]) / 256;
      breatheBlu = (b * breatheTable[sequenceIndex]) / 256;
      strip.setPixelColor(i, breatheRed, breatheGrn, breatheBlu);
    }
    strip.show();   // write all the pixels out
    delay(updatePeriod);
  }
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



