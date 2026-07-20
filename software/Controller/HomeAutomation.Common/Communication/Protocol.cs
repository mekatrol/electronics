namespace HomeAutomation.Common.Communication
{
    public class Protocol
    {
        /// <summary>
        /// Start of message
        /// </summary>
        public const char Som = '<';

        /// <summary>
        /// End of message
        /// </summary>
        public const char Eom = '>';

        /// <summary>
        /// Used for global messages (all should listen)
        /// </summary>
        public const ushort GlobalAddress = 0xFFFF;

        /// <summary>
        /// Used for sender address when no response is required
        /// </summary>
        public const ushort NoResponseAddress = 0x0000;

        [Flags]
        public enum MessageType : ushort
        {
            SetAddress = 0x0001,
            SetDateTime = 0x0002,
            InitStorage = 0x0003,
            GetStatus = 0x0004,
            FlashDumpPage = 0x0008,
            FlashReset = 0x0010,
            Nok = 0x4000,
            Ok = 0x8000
        }
    }
}
