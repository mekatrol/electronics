using static HomeAutomation.Common.Communication.Protocol;

namespace HomeAutomation.Common.Communication
{
    public class MessageQueue
    {
        private readonly object _threadSync = new();
        private readonly IDictionary<string, MessageQueueItem> _items = new Dictionary<string, MessageQueueItem>(StringComparer.OrdinalIgnoreCase);

        /// <summary>
        /// Add an item to the queue, will return false if the Id already exists in the queue
        /// </summary>
        public bool TryAdd(MessageQueueItem item)
        {
            lock (_threadSync)
            {
                if (_items.ContainsKey(item.Id)) return false;
                _items.Add(item.Id, item);
                return true;
            }
        }

        /// <summary>
        /// Remove an item from the queue, will return false if there
        /// are no items in the queue
        /// </summary>
        public bool TryRemove(out MessageQueueItem? item)
        {
            item = null;
            lock (_threadSync)
            {
                if (_items.Count == 0) return false;
                item = _items.Values.First();
                _items.Remove(item.Id);
                return true;
            }
        }

        /// <summary>
        /// Remove an item from the queue by id, will return false if there
        /// are no items in the queue with the matching id
        /// </summary>
        public bool TryRemove(string id)
        {
            lock (_threadSync)
            {
                if(_items.ContainsKey(id))
                {
                    _items.Remove(id);
                    return true;
                }
                return false;
            }
        }

        /// <summary>
        /// Try and get an unsent item from the queue, will
        /// return false if there are no unsent items in the queue
        /// </summary>
        public bool TryGetAndMarkSent(out MessageQueueItem? item)
        {
            item = null;
            lock (_threadSync)
            {
                if (_items.Count == 0) return false;
                item = _items.Values.FirstOrDefault(x => x.Sent == false);

                if (item != null)
                {
                    item.Sent = true;
                }

                return item != null;
            }
        }

        /// <summary>
        /// Try and get an expired item from the queue, will
        /// return false if there are no expired items in the queue
        /// </summary>
        public bool TryGetExpired(out MessageQueueItem? item)
        {
            var now = DateTime.Now;

            item = null;
            lock (_threadSync)
            {
                if (_items.Count == 0) return false;
                item = _items.Values.FirstOrDefault(x => x.Expiry <= now);

                if (item != null)
                {
                    _items.Remove(item.Id);
                }

                return item != null;
            }
        }

        /// <summary>
        /// Try and get an expired item from the queue, will
        /// return false if there are no expired items in the queue
        /// </summary>
        public bool TryGetById(string id, out MessageQueueItem? item)
        {
            item = null;
            lock (_threadSync)
            {
                if (!_items.ContainsKey(id)) return false;
                item = _items[id];

                if (item != null)
                {
                    _items.Remove(item.Id);
                }

                return item != null;
            }
        }

        /// <summary>
        /// Queue a message
        /// </summary>
        public string? QueueMessage(
            Message message,
            MessageType responseMessageType,
            TimeSpan responseTimeout,
            Action<Message, Message?>? handler)
        {
            var messageQueueItem = new MessageQueueItem(message, responseMessageType, handler, responseTimeout);

            // There is a special case when sending the set addr message to the global receiver address
            // because the response will come from the new address and not the global address
            if(message.MessageType == MessageType.SetAddress)
            {
                var setAddressMessage = (SetAddressMessage)message;
                messageQueueItem.Id = GenerateId(message.MessageType, message.SenderAddress, setAddressMessage.AddressToSet);
            }

            if (!TryAdd(messageQueueItem))
            {
                return null;
            }

            return messageQueueItem.Id;
        }

        /// <summary>
        /// Generate an ID usable in message queue
        /// </summary>
        public static string GenerateId(MessageType messageType, ushort senderAddr, ushort receiverAddr)
        {
            return $"{messageType}_{senderAddr}_{receiverAddr}";
        }
    }
}
