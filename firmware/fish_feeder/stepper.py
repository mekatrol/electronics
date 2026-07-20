from machine import Pin, disable_irq, enable_irq
import time

stepper1_enable_pin = Pin(0, Pin.OUT)
stepper1_step_pin = Pin(1)
stepper1_direction_pin = Pin(2, Pin.OUT)
stepper1_direction_pin.value(0)

stepper2_enable_pin = Pin(3, Pin.OUT)
stepper2_step_pin = Pin(4)
stepper2_direction_pin = Pin(5, Pin.OUT)
stepper2_direction_pin.value(0)

# To control speed just modify the amount/value of nop[dely amount 0-31].
@rp2.asm_pio(
    set_init=(rp2.PIO.OUT_HIGH),
    sideset_init=(rp2.PIO.OUT_LOW),
)
def do_steps():
    wrap_target()  # Main loop here
    pull().side(0x00)[0]  # Block until data pulled from OSR, side bits low
    mov(x, osr)  # OSR is loaded with the number of steps
    label("steps_loop")  # Loop here for number of steps
    set(pins, 0)[
        1
    ]  # Enable stepper driver (stepper1_enable_pin bit set low to stepper1_enable_pin) [One cycle delay after]
    nop().side(0x01)  # Set stepper1_step_pin bit
    nop()[3]  # 3 cycles delay
    nop()[3]  # 3 cycles delay
    nop().side(0x00)  # Clear stepper1_step_pin bit
    nop()[3]  # 3 cycles delay
    nop()[3]  # 3 cycles delay
    jmp(x_dec, "steps_loop")  # Loop until number of steps complete
    nop()[3]  # 3 cycles delay
    set(pins, 1)[
        1
    ]  # Disable stepper driver (stepper1_enable_pin bit set high to disable) [One cycle delay after]
    irq(noblock, rel(0))  # Raise IRQ to flag steps finished
    wrap()


# Flags to signal that the state machine is busy stepping
state_machine_busy_flags = [0, 0]


def is_sm_busy(sm):
    irq_state = disable_irq()  # Start of critical section
    sm_busy = state_machine_busy_flags[sm] == 1
    enable_irq(irq_state)  # End of critical section
    return sm_busy


def sm0_irq_handler(sm):
    # Clear busy flag
    state_machine_busy_flags[0] = 0


def sm1_irq_handler(sm):
    # Clear busy flag
    state_machine_busy_flags[1] = 0


stepper1 = rp2.StateMachine(
    0,
    do_steps,
    freq=200000,
    set_base=stepper1_enable_pin,
    sideset_base=stepper1_step_pin,
)
stepper1.irq(sm0_irq_handler)
stepper1.active(1)


stepper2 = rp2.StateMachine(
    1,
    do_steps,
    freq=200000,
    set_base=stepper2_enable_pin,
    sideset_base=stepper2_step_pin,
)
stepper2.irq(sm1_irq_handler)
stepper2.active(1)


def move(sm_num, step_direction, step_count):
    # Wait till state machine is not busy
    while is_sm_busy(sm_num):
        time.sleep(0.01)

    state_machine_busy_flags[sm_num] = 1

    if sm_num == 0:
        stepper1_direction_pin.value(step_direction)
        stepper1.put(step_count)
    elif sm_num == 1:
        stepper2_direction_pin.value(step_direction)
        stepper2.put(step_count)


def shake(sm_num):
    shakes = 20
    while shakes >= 0:
        shakes -= 1
        move(sm_num, 0, 400)
        move(sm_num, 1, 400)


def move_and_shake(sm_num):
    move(sm_num, 1, 2400)
    shake(sm_num)


turns = 7
while turns > 0:
    move_and_shake(0)
    move_and_shake(1)
    time.sleep(5)
    turns -= 1

while True:
    time.sleep(5)
