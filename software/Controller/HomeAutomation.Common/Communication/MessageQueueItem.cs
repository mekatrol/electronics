using static HomeAutomation.Common.Communication.Protocol;

namespace HomeAutomation.Common.Communication
{
    public class MessageQueueItem
    {
        public MessageQueueItem(Message messageToSend, MessageType responseMessageType, Action<Message, Message?>? handler, TimeSpan responseTimeout)
        {
            Id = MessageQueue.GenerateId(messageToSend.MessageType, messageToSend.SenderAddress, messageToSend.ReceiverAddress);
            MessageToSend = messageToSend;
            ResponseMessageType = responseMessageType;
            Handler = handler;
            ResponseTimeout = responseTimeout;
            Expiry = DateTime.Now + responseTimeout;
        }

        /// <summary>
        /// An ID that can be used to store the message in the hash table
        /// </summary>
        public string Id { get; set; }

        /// <summary>
        /// Set to true once the message has been sent
        /// </summary>
        public bool Sent { get; set; }

        /// <summary>
        /// The message to queue and send
        /// </summary>
        public Message MessageToSend { get; }

        /// <summary>
        /// The type of response message that is expected, e.g. Ok | GetStatus
        /// </summary>
        public MessageType ResponseMessageType { get; }

        /// <summary>
        /// The amount of time before the message times out 
        /// </summary>
        public TimeSpan ResponseTimeout { get; }

        public DateTime Expiry { get; }

        /// <summary>
        /// The handler that should process the received message.
        /// First message in action is the original sent message.
        /// Second message in action is the message recieved.
        /// Received message will be null if the response timed out.
        /// </summary>
        public Action<Message, Message?>? Handler { get; }
    }
}
