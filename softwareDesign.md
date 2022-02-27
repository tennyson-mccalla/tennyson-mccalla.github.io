# Software Design / Engineering Enhancement

## Narrative

*"People think it's this veneer — that the designers are handed this box and told, 'Make it look good!' That's not what we think design is. It's not just what it looks like and feels like. Design is how it works."* — Steve Jobs

By software design I mean how software works and not so much the aesthetics of how the end product of the software looks and feels (though that also has been enhanced).

The enhancement here was for an embedded systems project. The TI [CC3220SF-LAUNCHXL](https://www.ti.com/tool/CC3220SF-LAUNCHXL) offers a development kit with several example programs to give potential developers a feel for what the board can do. The example program that forms a basis for this project is called "gpiointerrupt.c". See the evolution of the project from [gpiointerrupt.c.orig]({{site.url}}/gpiointerrupt_CC3220SF_LAUNCHXL_nortos_ccs/gpiointerrupt.c.orig) to [gpiointerrupt.c.old]({{site.url}}/gpiointerrupt_CC3220SF_LAUNCHXL_nortos_ccs/gpiointerrupt.old) to present.

This is a [C program]({{site.url}}/gpiointerrupt_CC3220SF_LAUNCHXL_nortos_ccs/gpiointerrupt.c) that initializes and makes available the GPIO connected LEDs and buttons. On top that we've added initialization and use of the I2C interface, the UART interface, and the microsecond precision timers. The I2C peripheral here is acting as a thermometer and feeding sensor derived information to us via a function of the UART (i.e. DISPLAY). With the timers keeping accurate time an algorithm is made that fires off different functions at pre-determined time intervals.

Initially the plan for this enhancement was to capture the Celsius scale temperature information and then store the transformations of Celsius to Fahrenheit/Kelvin/ and even Rankine in a database. It turned out that it was easier to just do those conversions on the fly rather than try and store the calculated values in a database or file. While I failed to combine the already enhanced project and the [mongoc](https://mongoc.org) driver I still did change the way that the output was delivered.

Instead of being lost forever after being transmitted over UART the sensor information and variable values are now captured for longterm use and perusal in a file. For some reason the code used to work without all of the calls to DISPLAY I placed in the mainThread but it seems that they are now necessary in order for the loop not to get stuck. The [CSV file]({{site.url}}/database_stuff/temps_outfile.csv) forms an essential part of the Database artifact.

```C
/*
 * Copyright (c) 2015-2020, Texas Instruments Incorporated
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * *  Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 *
 * *  Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in the
 *    documentation and/or other materials provided with the distribution.
 *
 * *  Neither the name of Texas Instruments Incorporated nor the names of
 *    its contributors may be used to endorse or promote products derived
 *    from this software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
 * THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
 * PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
 * CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
 * EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
 * PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
 * OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
 * OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
 * EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

/*
 *  ======== gpiointerrupt.c ========
 */
#include <stdio.h>
#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <stdlib.h>
#include <unistd.h>

/* Driver Header files */
#include <ti/drivers/GPIO.h>

/* Driver configuration */
#include "ti_drivers_config.h"

#include <ti/drivers/I2C.h>
#include <ti/drivers/UART.h>
#include <ti/drivers/Timer.h>

#define DISPLAY(x) UART_write(uart, &output, x);

// I2C Global Variables
static const struct {
    uint8_t address;
    uint8_t resultReg;
    char *id;
} sensors[3] = {
                { 0x48, 0x0000, "11X" },
                { 0x49, 0x0000, "116" },
                { 0x41, 0x0001, "006" }
};
uint8_t txBuffer[1];
uint8_t rxBuffer[2];
I2C_Transaction i2cTransaction;

// Driver Handles - Global variables
I2C_Handle i2c;

// UART Global Variables
char output[64];
int bytesToSend;

// Driver Handles - Global variables
UART_Handle uart;

// Driver Handles - Global variables
Timer_Handle timer0;
volatile unsigned char TimerFlag = 0;

// global timer variable
int timer = 0;

// global value for heat on/off
bool heat = false;

// global value for setpoint
int setpoint;

// global value for seconds
int seconds = 0;

// file output
FILE *out_file; // write only

// Make sure you call initUART() before calling this function.
void initI2C(void)
{
    int8_t i, found;
    I2C_Params i2cParams;

    DISPLAY(snprintf(output, 64, "Initializing I2C Driver - "))

    // Init the driver
    I2C_init();

    // Configure the driver
    I2C_Params_init(&i2cParams);
    i2cParams.bitRate = I2C_400kHz;

    // Open the driver
    i2c = I2C_open(CONFIG_I2C_0, &i2cParams);
    if (i2c == NULL)
    {
        DISPLAY(snprintf(output, 64, "Failed\n\r"))
        while (1);
    }

    DISPLAY(snprintf(output, 64, "Passed\n\r"))

    // Boards were shipped with different sensors.
    // Welcome to the world of embedded systems.
    // Try to determine which sensor we have.
    // Scan through the possible sensor addresses

    /* Common I2C transaction setup */
    i2cTransaction.writeBuf = txBuffer;
    i2cTransaction.writeCount = 1;
    i2cTransaction.readBuf = rxBuffer;
    i2cTransaction.readCount = 0;

    found = false;
    for (i=0; i<3; ++i)
    {
        i2cTransaction.slaveAddress = sensors[i].address;
        txBuffer[0] = sensors[i].resultReg;
        DISPLAY(snprintf(output, 64, "Is this %s? ", sensors[i].id))
        if (I2C_transfer(i2c, &i2cTransaction))
        {
            DISPLAY(snprintf(output, 64, "Found\n\r"))
            found = true;
            break;
      }
      DISPLAY(snprintf(output, 64, "No\n\r"))
    }

    if (found)
    {
        DISPLAY(snprintf(output, 64, "Detected TMP%s I2C address:%x\n\r", sensors[i].id, i2cTransaction.slaveAddress))
    }
    else
    {
        DISPLAY(snprintf(output, 64, "Temperature sensor not found, contact professor\n\r"))
    }
}

int16_t readTemp(void)
{
    int16_t temperature = 0;

    i2cTransaction.readCount = 2;
    if (I2C_transfer(i2c, &i2cTransaction))
    {
        /*
         * Extract degrees C from the received data;
         * see TMP sensor datasheet
         */
        temperature = (rxBuffer[0] << 8) | (rxBuffer[1]);
        temperature *= 0.0078125;

        /*
        * If the MSB is set '1', then we have a 2's complement
        * negative value which needs to be sign extended
        */
        if (rxBuffer[0] & 0x80)
        {
        temperature |= 0xF000;
        }
    }
    else
    {
        DISPLAY(snprintf(output, 64, "Error reading temperature sensor (%d)\n\r",i2cTransaction.status))
        DISPLAY(snprintf(output, 64, "Please power cycle your board by unplugging USB and plugging back in.\n\r"))
    }

    return temperature;
}

void initUART(void)
{
    UART_Params uartParams;

    // Init the driver
    UART_init();

    // Configure the driver
    UART_Params_init(&uartParams);
    uartParams.writeDataMode = UART_DATA_BINARY;
    uartParams.readDataMode = UART_DATA_BINARY;
    uartParams.readReturnMode = UART_RETURN_FULL;
    uartParams.baudRate = 115200;

    // Open the driver
    uart = UART_open(CONFIG_UART_0, &uartParams);

    if (uart == NULL) {
        /* UART_open() failed */
        while (1);
    }
}

void timerCallback(Timer_Handle myHandle, int_fast16_t status)
{
    TimerFlag = 1;
    timer++;
}

void initTimer(void)
{
    Timer_Params params;

    // Init the driver
    Timer_init();

    // Configure the driver
    Timer_Params_init(&params);
    params.period = 100000;
    params.timerMode = Timer_CONTINUOUS_CALLBACK;
    params.periodUnits = Timer_PERIOD_US;
    params.timerCallback = timerCallback;

    // Open the driver
    timer0 = Timer_open(CONFIG_TIMER_0, &params);

    if (timer0 == NULL) {
        /* Failed to initialized timer */
        while (1) {}
    }

    if (Timer_start(timer0) == Timer_STATUS_ERROR) {
        /* Failed to start timer */
        while (1) {}
    }
}

/*
 *  ======== gpioButtonFxn0 ========
 *  Callback function for the GPIO interrupt on CONFIG_GPIO_BUTTON_0.
 *
 *  Note: GPIO interrupts are cleared prior to invoking callbacks.
 */
void gpioButtonFxn0(uint_least8_t index) {
    setpoint += 1;
}

/*
 *  ======== gpioButtonFxn1 ========
 *  Callback function for the GPIO interrupt on CONFIG_GPIO_BUTTON_1.
 *  This may not be used for all boards.
 *
 *  Note: GPIO interrupts are cleared prior to invoking callbacks.
 */
void gpioButtonFxn1(uint_least8_t index) {
    setpoint -= 1;
}

int getSetpoint(void) {
    return setpoint;
}

void write_file(int temperature, int setpoint, int heat, int seconds) {
   out_file = fopen("/Users/Tennyson/temps_outfile.csv", "a");//open for append
   fprintf(out_file, "%02d,%02d,%d,%04d\n", temperature, setpoint, heat, seconds); // write to file
   fclose(out_file);
}

/*
 *  ======== mainThread ========
 */
void *mainThread(void *arg0)
{
    int temperature; // initialize a local variable temperature

    /* Call driver init functions */
    GPIO_init();

    /* Configure the LED and button pins */
    GPIO_setConfig(CONFIG_GPIO_LED_0, GPIO_CFG_OUT_STD | GPIO_CFG_OUT_LOW);
    GPIO_setConfig(CONFIG_GPIO_BUTTON_0, GPIO_CFG_IN_PU | GPIO_CFG_IN_INT_FALLING);

    /* Turn off any user LEDs */
    GPIO_write(CONFIG_GPIO_LED_0, CONFIG_GPIO_LED_OFF);

    /* Install Button callback */
    GPIO_setCallback(CONFIG_GPIO_BUTTON_0, gpioButtonFxn0);

    /* Enable interrupts */
    GPIO_enableInt(CONFIG_GPIO_BUTTON_0);

    initUART(); // initialize the UART
    initI2C(); // // initialize the I2C

    /* Initialize timer */
    initTimer();

    /*
     *  If more than one input pin is available for your device, interrupts
     *  will be enabled on CONFIG_GPIO_BUTTON1.
     */
    if (CONFIG_GPIO_BUTTON_0 != CONFIG_GPIO_BUTTON_1) {
        /* Configure BUTTON1 pin */
        GPIO_setConfig(CONFIG_GPIO_BUTTON_1, GPIO_CFG_IN_PU | GPIO_CFG_IN_INT_FALLING);

        /* Install Button callback */
        GPIO_setCallback(CONFIG_GPIO_BUTTON_1, gpioButtonFxn1);
        GPIO_enableInt(CONFIG_GPIO_BUTTON_1);
            }

    while (1) {

        // because the timer variable increments every 100 000 microseconds or (100 ms)
        // the appropriate multiples will modulo to 0
        int s = timer % 2;
        if (timer < 10) {
        DISPLAY(snprintf(output, 64, "%d %% 2 = %d\n\r", timer, s))
        }
        if (!(timer % 2)) {
            if (timer < 10) {
            DISPLAY(snprintf(output, 64, "%d %% 2 = %d\n\r", timer, s))
            }

            // This was written to handle the case of restarts while connected
            // not getting the init temperature
            if (timer < 5) {
                setpoint = readTemp();
            } else {
                // getSetpoint does what it says. The setpoint value is affected
                // by buttons presses though and so must be checked every 0.2 s
                setpoint = getSetpoint();
            }
        }

        DISPLAY(snprintf(output, 64, "%d %% 5 = %d\n\r", timer, timer % 5))
        if (timer % 5 == 0) {
            DISPLAY(snprintf(output, 64, "%d %% 5 = %d\n\r", timer, timer % 5))
            temperature = readTemp(); // constantly reading the current temperature
            // if we've told it to turn the heat up (i.e. go higher than current
            // temperature) then heat should be true
            if (temperature < setpoint) {
                heat = true;
            } else {
                heat = false;
            }
        }

        if (timer % 100 == 0) {
        DISPLAY(snprintf(output, 64, "%d %% 10 = %d\n\r", timer, timer % 10))
        }
        if (timer % 10 == 0) {
            DISPLAY(snprintf(output, 64, "%d %% 10 = %d\n\r", timer, timer % 10))
            seconds++;

            // if we've told it to turn the heat up the light should go on and
            // heat should be true
            if (heat == true) {
                GPIO_write(CONFIG_GPIO_LED_0, CONFIG_GPIO_LED_ON);
            } else {
                // otherwise the light should be off
                GPIO_write(CONFIG_GPIO_LED_0, CONFIG_GPIO_LED_OFF);
            }
            // every second (or 10 x 0.1 s) increment the seconds counter and
            // print the following line out
            DISPLAY( snprintf(output, 64, "<%02d,%02d,%d,%04d>\n\r", temperature, setpoint, heat, seconds))
            write_file(temperature, setpoint, heat, seconds);
        }

        while (!TimerFlag) {}
        TimerFlag = 0;
    }
}
```

[tennyson-mccalla.github.io](https://tennyson-mccalla.github.io)
