Topic 16: Reusing Output Queues on WSE-3
========================================

On WSE-3, each output queue can only bind to a single color. Applications
which, on WSE-2, shared multiple colors on an output queue must be
modified to avoid running out of output queues on WSE-3.

WSE-3 allows the user to repurpose input/output queues with a
different color using ``@queue_flush``. This new feature allows reuse of
queues with a reasonable cost.

This example demonstrates how to reuse an output queue in the sender and
an input queue in the receiver on the WSE-3 architecture.

There are two PEs in this example, a sender (queue_flush_sender.csl) on
the left and a receiver (queue_flush_receiver.csl) on the right.
The sender sends two data sets to the receiver via the colors C10 and C12
. Both data sets are handled by the output queue 2.

The output queue must be drained before it can be reused. However, the
termination of a microthread only confirms that it pushed all of its data
into the output queue; the queue may not be empty yet. WSE-3 provides an
event handling mechanism to notify the user when an output queue becomes
empty.

Here is how it works:
The user calls ``@queue_flush(oq)`` after the microthread operation, for
example, ``@mov32`` which sends the data to an output queue ``oq``. When
``oq`` becomes empty, WSE-3 will trigger the special teardown task 29,
the same way a teardown wavelet does. The user has to register a handler,
``foo``, which can repurpose the output queue.
``@set_empty_queue_handler(foo, oq)`` binds the handler ``foo`` to the
output queue ``oq``. The handler ``foo`` does three things:
1. Reconfigure the color field of the output queue ``oq`` by
output_queue_config.encode_output_queue(oq, new color).
2. Execute logic that should follow reconfiguration of the output queue.
In the example, this is ``@activate(transmit2_id)``, which allows the
next data to be processed.
3. Clear the state of queue flush.
``queue_flush.exit(oq)`` is necessary, otherwise subsequent invocations
of the special teardown task 29 will call ``foo`` again.

The sender has the following sequence:
1. Send data1 to output queue ``oq`` which binds to color ``out_color1``.
2. ``done_transmit1`` is triggered when data1 has been sent to ``oq``.
3. ``done_transmit1`` reconfigures the color field of ``oq`` and calls
``@queue_flush(oq)``.
4. Whole data1 has been moved to the router, i.e. ``oq`` becomes empty.
5. The special teardown task 29 is triggered because ``oq`` is empty.
6. The special teardown task 29 calls the handler foo().
7. ``foo()`` binds ``oq`` with ``out_color2``.
8. ``foo()`` activates ``transmit2_id`` to send data2.
9. ``foo()`` calls ``queue_flush.exit()`` to clear the queue flush state.
10. ``transmit2_id`` is triggered to send out data2.
11. ``transmit2_id`` send data2 to output queue ``oq`` which binds to
color ``out_color2``.
12. ``exit()`` is triggered when data2 has been pushed into ``oq``.

Be careful not to issue ``@queue_flush(oq)`` before ``@mov32``, otherwise
it is possible that WSE-3 immediately triggers the special teardown task
29 when ``oq`` is empty because ``@mov32`` is not started yet to push
data into ``oq``.

The receiver receives two data sets from C10 and C12 sequentially. It is
safe to reuse the input queue. We just reconfigure input queue ``iq``
after data1 is received into ``result1``. Then we can continue receiving
data2 on the same ``iq``. This example does not need to use
``@queue_flush(iq)`` because ``iq`` is already empty at the time
``done_receive1`` is triggered. ``done_receive1`` can reconfigure ``iq``
safely.

The receiver introduces a dummy loop to increase the delay between
``@queue_flush(oq)`` and the special teardown task 29 so we can confirm
if the teardown task was triggered by emptiness of ``oq`` easily.

On WSE-2, multiple colors can share the same output queue without needing
to call the ``@queue_flush`` builtin (unlike on WSE-3). This is because,
on WSE-2, an output queue is not bound to a specific color, so data from
multiple colors can be sent to the same queue. Accordingly,
queue_flush_sender.csl omits ``@queue_flush(oq)`` when targeting WSE-2.
Likewise, queue_flush_receiver.csl does not call ``@queue_flush``: it
relies on the fact that the input queue is empty when the microthread
finishes, making it safe to reconfigure the input queue.

The filter enabled on color C12 accepts only the first two wavelets of
each 15-wavelet sequence. This behavior is enabled by passing the
``filter_enable`` parameter to encode_input_queue. As a result,
queue_flush_receiver.csl modifies only the first two entries of ``result2``.
