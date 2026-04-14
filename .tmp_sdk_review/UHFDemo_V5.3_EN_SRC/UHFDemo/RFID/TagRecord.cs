using RFID_API_ver1;
using System;
using System.ComponentModel;

namespace UHFDemo
{
    public class TagRecord : INotifyPropertyChanged
    {
        protected TagData RawRead = null;
        protected bool dataChecked = false;
        protected UInt32 serialNo = 0;
        protected string oldTemp = "null";
        private TagVendor vendor = TagVendor.NormalTag;
        public event PropertyChangedEventHandler PropertyChanged;
        protected DateTime Time;
        private double temperatureVal = 0.0;
        private double voltageVal = 0.0;
        private int readCount = 0;

        #region 0x79
        byte region;
        uint startFreq;
        byte endFreq;
        byte freqSpace;
        byte freqQuantity;
        #endregion 0x79

        public TagRecord(TagData newData, TagVendor chipType)
        {
            lock (new Object())
            {
                this.Time = DateTime.Now.ToLocalTime();
                this.readCount = newData.ReadCount;
                this.RawRead = newData;
                this.vendor = chipType;
                GetValueForSensorTag();
            }
        }

        /// <summary>
        /// Merge new tag read with existing one
        /// </summary>
        /// <param name="data">New tag read</param>
        public void Update(TagData mergeData, TagVendor chipType)
        {
            Time = DateTime.Now.ToLocalTime();
            readCount += mergeData.ReadCount;
            vendor = chipType;
            RawRead = mergeData;
            GetValueForSensorTag();
            OnPropertyChanged(null);
        }

        private void GetValueForSensorTag()
        {
            switch (vendor)
            {
                case TagVendor.JoharTag_1:
                    temperatureVal = getJoharTemp(RawRead.EPC, RawRead.Data);
                    break;
                //case TagVendor.FuDanTag_1_ReadTemp:
                //    temperatureVal = getFuDanTemp(RawRead);
                //    break;
                //case TagVendor.FuDanTag_1_ReadVoltage:
                //    voltageVal = getFuDanVoltage(RawRead);
                break;
                default:
                    break;
            }
        }

        public UInt32 SerialNumber
        {
            get { return serialNo; }
            set { serialNo = value; }
        }

        public int ReadCount
        {
            get { return readCount; }
            set { readCount = value; }
        }

        public string PC
        {
            get { return ByteUtils.ToHex(RawRead.PC, "", " "); }
        }

        public string EPC
        {
            get
            {
                return ByteUtils.ToHex(RawRead.EPC, "", " ");
            }
        }

        public string CRC
        {
            get { return ByteUtils.ToHex(RawRead.CRC, "", " "); }
        }

        public string Rssi
        {
            get { return string.Format("{0}", RawRead.Rssi); }
        }

        public string Freq
        {
            get { return string.Format("{0}", ((RawRead.Frequency / 1000.00f)).ToString("0.00")); }
        }

        public string Phase
        {
            get { return string.Format("{0}", RawRead.Phase); }
        }

        public string Antenna
        {
            get { return string.Format("{0}", RawRead.Antenna); }
        }

        public string Data
        {
            get
            {
                if (RawRead.Data.Length == 0)
                    return "null";
                return ByteUtils.ToHex(RawRead.Data, "", " ");
            }
        }
        //public string Data
        //{
        //    get { return RawRead.Data; }
        //}

        public string DataLen
        {
            get { return RawRead.DataLen.ToString(); }
        }

        //public string OpSuccessCount
        //{
        //    get { return RawRead.OpSuccessCount.ToString(); }
        //}

        public byte Region
        {
            get { return region; }
            set { region = value; }
        }
        public uint StartFreq
        {
            get { return startFreq; }
            set { startFreq = value; }
        }
        public byte EndFreq
        {
            get { return endFreq; }
            set { endFreq = value; }
        }
        public byte FreqSpace
        {
            get { return freqSpace; }
            set { freqSpace = value; }
        }
        public byte FreqQuantity
        {
            get { return freqQuantity; }
            set { freqQuantity = value; }
        }

        public string Temperature
        {
            get
            {
                return string.Format("{0}", temperatureVal);
            }
        }

        private double getFuDanTemp(TagData td)
        {
            double temp = 0.0;
            if (td.OpResult == ErrorCode.COMMAND_SUCCESS && td.Data != null && td.Data.Length == 2)
            {
                int index = 0;
                int AABB = ByteUtils.GetU16(td.Data, ref index);
                temp = AABB / 4.0;
            }
            else
            {
                return temperatureVal;
            }
            return Math.Round(temp, 2);
            //String strTemp = Math.Round(temp, 2).ToString();
            //return strTemp;
        }

        private double getFuDanVoltage(TagData td)
        {
            double temp = 0.0;
            if (td.OpResult == ErrorCode.COMMAND_SUCCESS && td.Data != null && td.Data.Length == 2)
            {
                int index = 0;
                int AABB = ByteUtils.GetU16(td.Data, ref index);
                temp = (AABB / 8192.0) * 2.5;
            }
            else
            {
                return voltageVal;
            }
            return Math.Round(temp, 2);
            //String strTemp = Math.Round(temp, 2).ToString();
            //return strTemp;
        }

        private double getJoharTemp(byte[] epc, byte[] data)
        {
            if (epc.Length <= 11 || data.Length < 4)
            {
                //Console.WriteLine("getTemp epc({0})={2}, data({1})={3}", epc.Length, data.Length, EPC, Data);
                return 0;
            }
            byte[] bytes = new byte[8];
            int writeIndex = 0;
            Array.Copy(epc, epc.Length - 4, bytes, 0, 4);
            writeIndex += 4;
            //Console.WriteLine(" Data: {0}", ByteUtils.ToHex(data, "", " "));
            Array.Copy(data, 0, bytes, writeIndex, 4);
            writeIndex += 4;

            //Console.WriteLine("getTemperature: {0}", ByteUtils.ToHex(bytes, "", " "));
            int senData = checkData(bytes);
            if (senData < 0)
            {
                //Console.WriteLine("Invalid sensor data!");
                return 0;
            }
            int D2 = (senData >> 3) & 0xFFFF;
            //Console.WriteLine("D2: {0}", D2);
            short Δ1 = (short)(((bytes[4] & 0xFF) << 8) | (bytes[5] & 0xFF));
            //Console.WriteLine("Δ1: {0}", Δ1);
            double temp = 11109.6 / (24 + (D2 + Δ1) / 375.3) - 290;
            if (temp > 125)
            {
                temp = temp * 1.2 - 25;
            }
            return Math.Round(temp, 2);
            //String strTemp = Math.Round(temp, 2).ToString();
            //return strTemp;
        }
        /**
         * Get senData
         *
         * @param bytes RawData
         * @return value >=0 : success
         * value = -1 : Failed to verify data length
         * value = -2 : Sensor data HEADER verification failed
         * value = -3 : Sensing data SEN_DATA[23:19] needs to be 00100b, otherwise the data is invalid
         * value = -4 : Sensor data verification failed
         * value = -5 : Detect chips that are not LTU32 version
         */
        private int checkData(byte[] bytes)
        {
            //Check data length
            if (bytes.Length != 8)
            {
                return -1;
            }
            //The sensor data HEADER needs to be 0xF, otherwise the data is invalid
            if (((bytes[0] >> 4) & 0x0F) != 0x0F)
            {
                return -2;
            }
            if (((bytes[2] >> 4) & 0x0F) != 0x0F)
            {
                return -2;
            }
            //Detection is LTU32 version of the chip,USR area 0x09[15:12] == 0010b
            if (((bytes[6] >> 4) & 0x0F) != 0x02)
            {
                return -5;
            }
            int senData = ((((bytes[0] & 0x0F) << 8) | (bytes[1] & 0xFF)) << 12) | ((bytes[2] & 0x0F) << 8) | (bytes[3] & 0xFF);
            //Sensor data SEN_DATA[23:19] needs to be 00100b, otherwise the data is invalid
            if (((senData >> 19) & 0x1F) != 0x04)
            {
                return -3;
            }
            //The sensor data shall be verified as follows, otherwise the data will be invalid
            if (((senData >> 2) & 1) != (~(((senData >> 14) & 1) ^ ((senData >> 11) & 1) ^ ((senData >> 8) & 1) ^ ((senData >> 5) & 1)) & 1))
            {
                return -4;
            }
            if (((senData >> 1) & 1) != (~(((senData >> 13) & 1) ^ ((senData >> 10) & 1) ^ ((senData >> 7) & 1) ^ ((senData >> 4) & 1)) & 1))
            {
                return -4;
            }
            if ((senData & 1) != (~(((senData >> 12) & 1) ^ ((senData >> 9) & 1) ^ ((senData >> 6) & 1) ^ ((senData >> 3) & 1)) & 1))
            {
                return -4;
            }
            return senData;
        }

        public ErrorCode OperationResult
        {
            get { return RawRead.OpResult; }
        }

        //public string Temperature
        //{
        //    get
        //    {
        //        if (vendor == TagVendor.NormalTag)
        //        {
        //            return "null";
        //        }
        //        bool checkTemp = RawRead.Temperature.Equals("null");
        //        return (checkTemp == false ? RawRead.Temperature : oldTemp);
        //    }
        //}

        #region INotifyPropertyChanged Members
        private void OnPropertyChanged(string name)
        {
            PropertyChangedEventArgs td = new PropertyChangedEventArgs(name);
            try
            {
                if (null != PropertyChanged)
                {
                    PropertyChanged(this, td);
                }
            }
            finally
            {
                td = null;
            }
        }
        #endregion
    }
}