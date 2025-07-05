I don't have a raildriver and needed a way to easily map input axis and buttons to controls accepted by Run8. This program translates assigned axis / buttons into UDP packets that the simulator expects. So far, I've tested it with a standard xbox controller and a flight simulator joystick. The controls behave mostly correct; however there may still be some inconsistencies or weird bugs. (This is a computer program made by a computer, after all). Notably the dynamic brake axis seems a bit hard to get right, but in it's current state it should be functional.

From the top, the simulator IP can stay as the default loopback address (127.0.0.1). Passing the UDP packets over intranet should work in theory, but it has not been tested.
Change the UDP port to match what it is set to in run8.
Map your inputs
Press "Start UDP" at the bottom.

Your mileage may vary; if there's any suggestions let me know and I'll tell the AI to do it ;)
Thanks, and have fun! Please let me know if this tool was of any use for you!
