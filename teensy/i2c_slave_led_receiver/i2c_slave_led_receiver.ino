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

// function that executes whenever data is received from master
// this function is registered as an event, see setup()
void receiveEvent(int howMany)
{
  while(1 < Wire.available()) // loop through all but the last
  {
    char c = Wire.read(); // receive byte as a character
    Serial.print("h: ");         // print the character
    Serial.print(c);         // print the character
  }
  int x = Wire.read();    // receive byte as an integer
  Serial.print("t: ");         // print the character
  Serial.println(x);         // print the integer

  paintLeds(x);
  return;
}


