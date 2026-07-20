namespace HomeAutomation.Common.Communication
{
    public class FlashResetMessage : Message
    {
        public FlashResetMessage(ushort receiverAddress = Protocol.GlobalAddress, ushort senderAddress = Protocol.NoResponseAddress)
                            : base(Protocol.MessageType.FlashDumpPage, receiverAddress, senderAddress)
        {
        }
    }
}
