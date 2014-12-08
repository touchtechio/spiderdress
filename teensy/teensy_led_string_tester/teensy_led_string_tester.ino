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

#define LED_COUNT 20
#define LED_BARS 2
int ledsPerBar = LED_COUNT / LED_BARS;



// setup
Adafruit_NeoPixel leftStrip = Adafruit_NeoPixel(LED_COUNT, NEOPIXEL_RIGHT_PIN, NEO_GRB + NEO_KHZ800);
Adafruit_NeoPixel rightStrip = Adafruit_NeoPixel(LED_COUNT, NEOPIXEL_LEFT_PIN, NEO_GRB + NEO_KHZ800);



// Color Definitions
struct RGB {
  byte r;
  byte g;
  byte b;
};

int current_led_count = LED_COUNT;

int black = leftStrip.Color(0, 0, 0);   // leds off
RGB current_color = {0, 0, 127};




void setup()
{

  Serial.begin(9600);           // start serial for output

  // bring up led driver
  leftStrip.begin();
  rightStrip.begin();
  show(); // Initialize all pixels to 'off'

  // ???
  pinMode(0,OUTPUT);             // for verification
  digitalWrite(11, HIGH);
  paintLeds(12);

}


void loop() {
  rainbow(20);
  rainbowCycle(20);
  theaterChaseRainbow(50);
}

// Fill the dots one after the other with a color
void colorWipe(uint32_t c, uint8_t wait) {
  for(uint16_t i=0; i<LED_COUNT; i++) {
      setPixelColor(i, c);
      show();
      delay(wait);
  }
}

void rainbow(uint8_t wait) {
  uint16_t i, j;

  for(j=0; j<256; j++) {
    for(i=0; i<LED_COUNT; i++) {
      setPixelColor(i, Wheel((i+j) & 255));
    }
    show();
    delay(wait);
  }
}

// Slightly different, this makes the rainbow equally distributed throughout
void rainbowCycle(uint8_t wait) {
  uint16_t i, j;

  for(j=0; j<256*5; j++) { // 5 cycles of all colors on wheel
    for(i=0; i< LED_COUNT; i++) {
      setPixelColor(i, Wheel(((i * 256 / LED_COUNT) + j) & 255));
    }
    show();
    delay(wait);
  }
}

//Theatre-style crawling lights.
void theaterChase(uint32_t c, uint8_t wait) {
  for (int j=0; j<10; j++) {  //do 10 cycles of chasing
    for (int q=0; q < 3; q++) {
      for (int i=0; i < LED_COUNT; i=i+3) {
        setPixelColor(i+q, c);    //turn every third pixel on
      }
      show();
     
      delay(wait);
     
      for (int i=0; i < LED_COUNT; i=i+3) {
        setPixelColor(i+q, 0);        //turn every third pixel off
      }
    }
  }
}

//Theatre-style crawling lights with rainbow effect
void theaterChaseRainbow(uint8_t wait) {
  for (int j=0; j < 256; j++) {     // cycle all 256 colors in the wheel
    for (int q=0; q < 3; q++) {
        for (int i=0; i < LED_COUNT; i=i+3) {
          setPixelColor(i+q, Wheel( (i+j) % 255));    //turn every third pixel on
        }
        show();
       
        delay(wait);
       
        for (int i=0; i < LED_COUNT; i=i+3) {
          setPixelColor(i+q, 0);        //turn every third pixel off
        }
    }
  }
}

// Input a value 0 to 255 to get a color value.
// The colours are a transition r - g - b - back to r.
uint32_t Wheel(byte WheelPos) {
  WheelPos = 255 - WheelPos;
  if(WheelPos < 85) {
   return rightStrip.Color(255 - WheelPos * 3, 0, WheelPos * 3);
  } else if(WheelPos < 170) {
    WheelPos -= 85;
   return rightStrip.Color(0, WheelPos * 3, 255 - WheelPos * 3);
  } else {
   WheelPos -= 170;
   return rightStrip.Color(WheelPos * 3, 255 - WheelPos * 3, 0);
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
  rightStrip.setPixelColor(n, g, r, b);
  leftStrip.setPixelColor(n, g, r, b);
  return;
}

void setPixelColor(uint16_t n, uint32_t c) {
  rightStrip.setPixelColor(n, c);
  leftStrip.setPixelColor(n, c);
}


// called to update leds
void paintLeds(int ledCount) { 

  for (int i = 0; i < ledsPerBar; i++) {
    for (int bar = 0; bar < LED_BARS; bar++) {

      int ledIndex = i+ledsPerBar*bar;

      if (ledCount > i) {
        // leds on
        setPixelColor(ledIndex, leftStrip.Color(  current_color.r, current_color.g, current_color.b));
      } 
      else {
        // leds off
        setPixelColor(ledIndex, leftStrip.Color( current_color.r, current_color.g, current_color.b / 7 ));
      }
    }
  }

  show();
}


