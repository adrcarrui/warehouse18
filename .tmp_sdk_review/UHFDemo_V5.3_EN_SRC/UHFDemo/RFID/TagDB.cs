using RFID_API_ver1;
using System;
using System.ComponentModel;
using System.Collections.Generic;

namespace UHFDemo
{
    public class TagDB
    {
        private TagRecordBindingList _tagList = new TagRecordBindingList();
        private Dictionary<string, TagRecord> EpcIndex = new Dictionary<string, TagRecord>();
        private long uniqueTagcounts = 0;
        private long totalReadCounts = 0;
        private long totalCommandTime = 0;
        private long roundCommandDuration = 0;
        private long roundRead = 0;
        private long roundReadRate = 0;

        public TagDB()
        {
            // GUI can't keep up with fast updates, so disable automatic triggers
            //_tagList.RaiseListChangedEvents = false;
        }

        public BindingList<TagRecord> TagList
        {
            get { return _tagList; }
        }
        public long UniqueTagCounts
        {
            get { return uniqueTagcounts; }
        }
        public long TotalReadCounts
        {
            get { return totalReadCounts; }
        }

        public long TotalCommandTime
        {
            get { return totalCommandTime; }
        }

        public long RoundCommandDuration
        {
            get { return roundCommandDuration; }
        }

        public long RoundTotalRead
        {
            get { return roundRead; }
        }

        public long RoundReadRate
        {
            get { return roundReadRate; }
        }

        private bool rssiSet = false;
        private uint keyLen = 0;
        private TagVendor chipType = TagVendor.NormalTag;

        public int MinRSSI { get; internal set; }
        public int MaxRSSI { get; internal set; }

        public void Clear()
        {
            lock (_tagList)
            {
                EpcIndex.Clear();
                _tagList.Clear();
                // Clear doesn't fire notifications on its own
                _tagList.ResetBindings();

                rssiSet = false;
                MinRSSI = 0;
                MaxRSSI = 0;
                roundRead = 0;
                roundReadRate = 0;
                roundCommandDuration = 0;
                totalReadCounts = 0;
                totalCommandTime = 0;
                uniqueTagcounts = 0;
            }
        }

        public void Add(TagData addData)
        {
            lock (_tagList)
            {
                string key = null;
                if (keyLen == 0)
                {
                    key = ByteUtils.ToHex(addData.EPC, "", "");
                }
                else
                {
                    key = ByteUtils.ToHex(addData.EPC, "", "").Substring(0, (int)keyLen);
                }
                uniqueTagcounts = 0;
                totalReadCounts = 0;
                if (!EpcIndex.ContainsKey(key))
                {
                    TagRecord value = new TagRecord(addData, chipType);
                    value.SerialNumber = (uint)EpcIndex.Count + 1;

                    _tagList.Add(value);
                    EpcIndex.Add(key, value);
                    //Call this method to calculate total tag reads and unique tag read counts 
                    UpdateTagCountTextBox(EpcIndex);
                    UpdateMinMaxRssi(addData.Rssi);

                    DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, "Add({0}) {1}", value.SerialNumber, value.EPC);
                    Repaint();
                }
                else
                {
                    EpcIndex[key].Update(addData, chipType);
                    UpdateTagCountTextBox(EpcIndex);
                }
            }
        }

        private void UpdateMinMaxRssi(int rssi)
        {
            if (rssiSet)
            {
                if (rssi < MinRSSI)
                {
                    MinRSSI = rssi;
                }

                if (rssi > MaxRSSI)
                {
                    MaxRSSI = rssi;
                }
            }
            else
            {
                rssiSet = true;
                MinRSSI = rssi;
                MaxRSSI = rssi;
            }
        }

        //Calculate total tag reads and unique tag reads.
        public void UpdateTagCountTextBox(Dictionary<string, TagRecord> EpcIndex)
        {
            uniqueTagcounts = EpcIndex.Count;
            TagRecord[] dataRecord = new TagRecord[EpcIndex.Count];
            EpcIndex.Values.CopyTo(dataRecord, 0);
            totalReadCounts = 0;
            for (int i = 0; i < dataRecord.Length; i++)
            {
                totalReadCounts += dataRecord[i].ReadCount;
            }
        }

        public void UpdateTotalDuration(int duration)
        {
            totalCommandTime += duration;
        }

        /// <summary>
        /// Manually release change events
        /// </summary>
        public void Repaint()
        {
            lock (_tagList)
            {
                //if(!_tagList.RaiseListChangedEvents)
                {
                    _tagList.RaiseListChangedEvents = true;

                    //Causes a control bound to the BindingSource to reread all the items in the list and refresh their displayed values.
                    _tagList.ResetBindings();

                    _tagList.RaiseListChangedEvents = false;
                }
            }
        }

        public void EnableAutomaticTriggers()
        {
            //DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, "EnableAutomaticTriggers");
            lock (_tagList)
            {
                _tagList.RaiseListChangedEvents = true;
            }
        }

        public void DisableAutomaticTriggers()
        {
            //DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, "DisableAutomaticTriggers");
            lock (_tagList)
            {
                // GUI can't keep up with fast updates, so disable automatic triggers
                _tagList.RaiseListChangedEvents = false;
            }
        }

        internal void SetSensorTag(TagVendor tagVendor)
        {
            switch (tagVendor)
            {
                case TagVendor.JoharTag_1:
                    {
                        keyLen = 4;
                        chipType = TagVendor.JoharTag_1;
                    }
                    break;
                //case TagVendor.FuDanTag_1_ReadTemp:
                //    {
                //        keyLen = 0;
                //        chipType = TagVendor.FuDanTag_1_ReadTemp;
                //    }
                //    break;
                //case TagVendor.FuDanTag_1_ReadVoltage:
                //    {
                //        keyLen = 0;
                //        chipType = TagVendor.FuDanTag_1_ReadVoltage;
                //    }
                //    break;
                case TagVendor.NormalTag:
                default:
                    keyLen = 0;
                    chipType = TagVendor.NormalTag;
                    break;
            }
        }
    }
}