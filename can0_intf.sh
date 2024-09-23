#!/bin/bash
INTF_NO=0

echo " CAN${INTF_NO} interface configuration "
CANRunning=`ifconfig | grep -c can${INTF_NO}`

do_start()
{
        if [ $CANRunning -eq 1 ]; then
                echo "can${INTF_NO} deactivate"
                sudo ip link set can${INTF_NO} down
        fi

        echo " CAN${INTF_NO} interface start "
        sudo ip link set can${INTF_NO} txqueuelen 1000
        sudo ip link set can${INTF_NO} up type can bitrate 250000 sample-point 0.80 restart-ms 300
}

do_stop()
{
        echo "can${INTF_NO} deactivate"
        ip link set can${INTF_NO} down
}

case $1 in
        start)
                do_start
                ;;
        stop)
                do_stop
                ;;
esac

echo " CAN${INTF_NO} configuration complete"