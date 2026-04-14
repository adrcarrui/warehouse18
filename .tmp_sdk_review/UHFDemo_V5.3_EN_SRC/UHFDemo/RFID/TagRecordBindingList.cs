using System;
using System.ComponentModel;

namespace UHFDemo
{
    public class TagRecordBindingList : SortableBindingList<TagRecord>
    {
        protected override Comparison<TagRecord> GetComparer(PropertyDescriptor prop)
        {
            Comparison<TagRecord> comparer = null;
            switch (prop.Name)
            {
                case "SerialNumber":
                    comparer = new Comparison<TagRecord>(delegate (TagRecord a, TagRecord b)
                    {
                        return (int)(a.SerialNumber - b.SerialNumber);
                    });
                    break;
                case "ReadCount":
                    comparer = new Comparison<TagRecord>(delegate (TagRecord a, TagRecord b)
                    {
                        return a.ReadCount - b.ReadCount;
                    });
                    break;
                case "PC":
                    comparer = new Comparison<TagRecord>(delegate (TagRecord a, TagRecord b)
                    {
                        return String.Compare(a.PC, b.PC);
                    });
                    break;
                case "EPC":
                    comparer = new Comparison<TagRecord>(delegate (TagRecord a, TagRecord b)
                    {
                        return String.Compare(a.EPC, b.EPC);
                    });
                    break;
                case "CRC":
                    comparer = new Comparison<TagRecord>(delegate (TagRecord a, TagRecord b)
                    {
                        return String.Compare(a.CRC, b.CRC);
                    });
                    break;
                case "Rssi":
                    comparer = new Comparison<TagRecord>(delegate (TagRecord a, TagRecord b)
                    {
                        return String.Compare(a.Rssi, b.Rssi);
                    });
                    break;
                //case "Freq":
                //    comparer = new Comparison<TagRecord>(delegate (TagRecord a, TagRecord b)
                //    {
                //        return String.Compare(a.Freq, b.Freq);
                //    });
                //    break;
                case "Freq":
                    comparer = new Comparison<TagRecord>(delegate (TagRecord a, TagRecord b)
                    {
                        return String.Compare(a.Freq, b.Freq);
                    });
                    break;
                case "Phase":
                    comparer = new Comparison<TagRecord>(delegate (TagRecord a, TagRecord b)
                    {
                        return String.Compare(a.Phase, b.Phase);
                    });
                    break;
                case "Antenna":
                    comparer = new Comparison<TagRecord>(delegate (TagRecord a, TagRecord b)
                    {
                        return String.Compare(a.Antenna, b.Antenna);
                    });
                    break;
                case "Data":
                    comparer = new Comparison<TagRecord>(delegate (TagRecord a, TagRecord b)
                    {
                        return String.Compare(a.Data, b.Data);
                    });
                    break;
                case "DataLen":
                    comparer = new Comparison<TagRecord>(delegate (TagRecord a, TagRecord b)
                    {
                        return String.Compare(a.DataLen, b.DataLen);
                    });
                    break;
                //case "OpSuccessCount":
                //    comparer = new Comparison<TagRecord>(delegate (TagRecord a, TagRecord b)
                //    {
                //        return String.Compare(a.OpSuccessCount, b.OpSuccessCount);
                //    });
                //    break;
                case "Region":
                    comparer = new Comparison<TagRecord>(delegate (TagRecord a, TagRecord b)
                    {
                        return a.Region - b.Region;
                    });
                    break;
                case "StartFreq":
                    comparer = new Comparison<TagRecord>(delegate (TagRecord a, TagRecord b)
                    {
                        return (int)(a.StartFreq - b.StartFreq);
                    });
                    break;
                case "EndFreq":
                    comparer = new Comparison<TagRecord>(delegate (TagRecord a, TagRecord b)
                    {
                        return a.EndFreq - b.EndFreq;
                    });
                    break;
                case "FreqSpace":
                    comparer = new Comparison<TagRecord>(delegate (TagRecord a, TagRecord b)
                    {
                        return a.FreqSpace - b.FreqSpace;
                    });
                    break;
                case "FreqQuantity":
                    comparer = new Comparison<TagRecord>(delegate (TagRecord a, TagRecord b)
                    {
                        return a.FreqQuantity - b.FreqQuantity;
                    });
                    break;
                case "Temperature":
                    comparer = new Comparison<TagRecord>(delegate (TagRecord a, TagRecord b)
                    {
                        return String.Compare(a.Temperature, b.Temperature);
                    });
                    break;
            }
            return comparer;
        }
    }
}