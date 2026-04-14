using RFID_API_ver1;
using System;
using System.IO;
using System.Net;
using System.Data;
using System.Text;
using System.Drawing;
using System.IO.Ports;
using System.Resources;
using System.Threading;
using System.Management;
using System.Net.Sockets;
using System.Diagnostics;
using System.Windows.Forms;
using System.Globalization;
using System.Windows.Threading;
using System.Collections.Generic;

namespace UHFDemo
{
    public partial class UHFDemo : Form
    {
        private Reader reader;
        //Real-time inventory locking operation
        private bool m_bLockTab = false;
        //ISO18000 Tag continuous inventory identification
        private bool m_bContinue = false;
        private bool m_bDisplayLog = false;
        //Record the number of ISO18000 Tag cycle writes
        private int m_nLoopTimes = 0;
        //Record the number of characters written to the ISO18000 tag
        private int m_nBytes = 0;
        //Record the number of times the ISO18000 tag has been cycled
        private int m_nLoopedTimes = 0;
        private int m_InvExeTime = -1;
        private int m_InvCmdInterval = 0;
        private bool m_getOutputPower = false;
        private bool m_setOutputPower = false;
        private bool m_setWorkAnt = false;
        private bool m_getWorkAnt = false;
        private CheckBox[] fast_inv_ants = null;
        private TextBox[] fast_inv_stays = null;
        private TextBox[] fast_inv_temp_pows = null;
        TagDB tagdb = null;
        TagDB tagdbTmp = null;
        TagDB tagOpDb = null;
        bool isFastInv = false;
        bool doingFastInv = false;
        bool Inventorying = false;
        bool isRealInv = false;
        bool doingRealInv = false;
        bool isBufferInv = false;
        bool doingBufferInv = false;
        bool needGetBuffer = false;
        private int tagbufferCount = 0;
        private bool ReverseTarget = false;
        private int stayBTimes = 0;
        private bool invTargetB = false;
        bool useAntG1 = true;

        /// <summary>
        /// Define a variable for the inventory test log
        /// </summary>
        TextWriter transportLogFile = null;
        uint inventory_times = 1;
        RadioButton[] sessionArr = null;
        RadioButton[] targetArr = null;
        RadioButton[] selectFlagArr = null;
        DispatcherTimer dispatcherTimer = null;
        DispatcherTimer readratePerSecond = null;
        DispatcherTimer invCmdIntervalTimer = null;
        //Record the inventory start time
        DateTime startInventoryTime = DateTime.Now;
        DateTime beforeCmdExecTime = DateTime.Now;
        //The time elapsed between the beginning of the inventory and this moment
        public double elapsedTime = 0.0; 
        List<string> antLists = null;
        private int WriteTagCount = 0;
        //store for setting workAntenna and inv
        byte btWorkAntenna = 0;
        int curWorkAntenna = 0;


        //  default val
        private ReaderType readerType = ReaderType.SERIAL;
        private Channels channels = Channels.One;

        private bool isTemppower;
        private List<Antenna> antList = null;

        private TextBox[] txtbxOutputPows = null;
        private Label[] labPows = null;


        private TagMaskDB tagMaskDB = null;

        private static string[] R2000ProfileID = { "配置0：Tari 25uS; FM0 40KHz", "配置1(推荐且为默认)：Tari 25uS; Miller 4 250KHz",
                                                   "配置2：Tari 25uS; Miller 4 300KHz", "配置3：Tari 6.25uS; FM0 400KHz"};

        private static string[] E710ProfileID = { "配置1：PR-ASK, Tari 7.5uS，Miller 2 640KHz", "配置3：PR-ASK, Tari 20uS，Miller 2 320KHz", "配置5：PR-ASK, Tari 20uS，Miller 4 320KHz",
        "配置7(推荐且默认)：PR-ASK, Tari 20uS，Miller 4 250KHz", "配置11：PR-ASK, Tari 7.5uS,FM0 640KHz", "配置12：PR-ASK, Tari 15uS,Miller 2 320KHz", "配置13：PR-ASK, Tari 20uS,Miller 8 160KHz", 
        "配置15：PR-ASK, Tari 7.5uS,Miller 4 640KHz", "配置302：PR-ASK, Tari 7.5uS,Miller 1 640KHz", "配置103：DSB, Tari 6.25uS, Miller 1 640KHz", "配置120：DSB, Tari 6.25uS, Miller 2 640KHz", 
        "配置222：PR-ASK, Tari 20uS，Miller 2 320KHz", "配置323：PR-ASK, Tari 7.5uS，Miller 2 640KHz", "配置223：PR-ASK, Tari 15uS，Miller 2 320KHz", "配置241：PR-ASK, Tari 20uS，Miller 4 320KHz", 
        "配置244：PR-ASK, Tari 20uS，Miller 4 250KHz", "配置344：PR-ASK, Tari 7.5uS，Miller 4 640KHz(PIE 2)", "配置345：PR-ASK, Tari 7.5uS，Miller 4 640KHz(PIE 1.5)", "配置285：PR-ASK, Tari 20uS，Miller 8 160KHz", 
        "配置202：PR-ASK, Tari 15uS，Miller 1 426KHz"};

        private static int[] BaudRateR2000 = { 38400, 115200};
        private static int[] BaudRateE710 = { 38400, 115200, 256000, 512000, 750000, 921600 };

        private int ModelFlag = 0;  // R2000 = 1; E710 = 2;
        private bool FreqRegionFlag = false;
        private bool LimitFlag = false;
        private bool IceTest = false;
        private System.Timers.Timer InvTime = null;
        private System.Timers.Timer OATime = null;
        private int TmpExcute = 0;
        private bool InvOrNot = false;
        private bool CommunicateFlag = false;
        private System.Timers.Timer MonitorTime = null;
        DateTime startCmdTime = DateTime.Now;
        private System.Timers.Timer StartCmdTime = null;
        private bool MulAntReadTag = false;
        //  LogInfo Flag
        //  
        public enum HistoryType
        {
            Normal = 0x00,          //  Color.Indigo
            Success = 0x01,         //  Color.blue
            Failed = 0x02,          //  Color.red
        }


        #region FindResource
        ResourceManager LocRM;
        private void initFindResource()
        {
            LocRM = new ResourceManager("UHFDemo.WinFormString_en", typeof(UHFDemo).Assembly);
        }

        public string FindResource(string key)
        {
            try
            {
                return LocRM.GetString(key);
            }
            catch (Exception ex)
            {
                throw new Exception(string.Format("{0}= {1}, {2}", FindResource("tipNotContainsKey"), key, ex.Message));
            }
        }
        #endregion //FindResource

        public UHFDemo()
        {
            //Thread.CurrentThread.CurrentUICulture = new CultureInfo("zh-CN");//en
            Thread.CurrentThread.CurrentUICulture = new CultureInfo("en-US");//en
            InitializeComponent();
            initFindResource();

#if false

            Text = string.Format("{0}{1}.{2}.{3}",
                FindResource("DemoName"),
                System.Reflection.Assembly.GetExecutingAssembly().GetName().Version.Major,
                System.Reflection.Assembly.GetExecutingAssembly().GetName().Version.Minor,
                System.Reflection.Assembly.GetExecutingAssembly().GetName().Version.Revision);

#else
            Text = string.Format("{0}{1}.{2}",
                  FindResource("DemoName"),
                  System.Reflection.Assembly.GetExecutingAssembly().GetName().Version.Major,
                  System.Reflection.Assembly.GetExecutingAssembly().GetName().Version.Minor);
#endif
            //if((System.Reflection.Assembly.GetExecutingAssembly().GetName().Version.Revision % 2) == 0)
            //{
            groupBox32.Visible = false;
            //}

            DoubleBuffered = true;

            fast_inv_ants = new CheckBox[] { 
                chckbx_fast_inv_ant_1, chckbx_fast_inv_ant_2, chckbx_fast_inv_ant_3, chckbx_fast_inv_ant_4,
                chckbx_fast_inv_ant_5, chckbx_fast_inv_ant_6, chckbx_fast_inv_ant_7, chckbx_fast_inv_ant_8,
                chckbx_fast_inv_ant_9, chckbx_fast_inv_ant_10, chckbx_fast_inv_ant_11, chckbx_fast_inv_ant_12,
                chckbx_fast_inv_ant_13, chckbx_fast_inv_ant_14, chckbx_fast_inv_ant_15, chckbx_fast_inv_ant_16
            };

            fast_inv_stays = new TextBox[] { 
                txt_fast_inv_Stay_1, txt_fast_inv_Stay_2, txt_fast_inv_Stay_3, txt_fast_inv_Stay_4,
                txt_fast_inv_Stay_5, txt_fast_inv_Stay_6, txt_fast_inv_Stay_7, txt_fast_inv_Stay_8,
                txt_fast_inv_Stay_9, txt_fast_inv_Stay_10, txt_fast_inv_Stay_11, txt_fast_inv_Stay_12,
                txt_fast_inv_Stay_13,txt_fast_inv_Stay_14, txt_fast_inv_Stay_15, txt_fast_inv_Stay_16
            };

            fast_inv_temp_pows = new TextBox[] {
                tv_temp_pow_1, tv_temp_pow_2, tv_temp_pow_3, tv_temp_pow_4, tv_temp_pow_5, tv_temp_pow_6, tv_temp_pow_7, tv_temp_pow_8,
                tv_temp_pow_9, tv_temp_pow_10, tv_temp_pow_11, tv_temp_pow_12, tv_temp_pow_13, tv_temp_pow_14, tv_temp_pow_15, tv_temp_pow_16
            };

            foreach(TextBox tb in fast_inv_temp_pows)
            {
                tb.Text = string.Format("{0}", 20);
                tb.Enabled = false;
            }

            bindInvAntTableEvents();

            sessionArr = new RadioButton[] { radio_btn_S0, radio_btn_S1, radio_btn_S2, radio_btn_S3 };
            targetArr = new RadioButton[] { radio_btn_target_A, radio_btn_target_B };
            selectFlagArr = new RadioButton[] { radio_btn_sl_00, radio_btn_sl_01, radio_btn_sl_02, radio_btn_sl_03 };

            radio_btn_S1.Checked = true;
            radio_btn_target_A.Checked = true;
            radio_btn_sl_00.Checked = true;

            initRealInvAnts();
            radio_btn_realtime_inv.Checked = true;
            
            dispatcherTimer = new DispatcherTimer();
            dispatcherTimer.Interval = TimeSpan.FromMilliseconds(50);
            dispatcherTimer.Tick += new EventHandler(dispatcherTimer_Tick);

            readratePerSecond = new DispatcherTimer();
            readratePerSecond.Interval = TimeSpan.FromMilliseconds(50);
            readratePerSecond.Tick += new EventHandler(readRatePerSec_Tick);

            rdbEpc.Checked = true;

            txtbxOutputPows = new TextBox[] { 
                tb_outputpower_1, tb_outputpower_2, tb_outputpower_3, tb_outputpower_4, 
                tb_outputpower_5, tb_outputpower_6, tb_outputpower_7, tb_outputpower_8, 
                tb_outputpower_9, tb_outputpower_10, tb_outputpower_11, tb_outputpower_12, 
                tb_outputpower_13, tb_outputpower_14, tb_outputpower_15, tb_outputpower_16 };

            antList = new List<Antenna>();
        }

        private void R2000UartDemo_Load(object sender, EventArgs e)
        {
            //Sets the validity of interface elements
            SetFormEnable(false);
            radio_btn_rs232.Checked = true;
            antType4.Checked = true; 
            rb_R2000.Checked = true;
            //this.tabControl_baseSettings.TabPages.Remove(this.tabPage4);
            //this.tabCtrMain.TabPages.Remove(this.PagSpecialFeature);
            this.tabControl_baseSettings.TabPages.Remove(this.tabPage5);


            //Initializes the default configuration of the connection reader
            RefreshComPorts();


            ipIpServer.IpAddressStr = FindResource("DefaultIP");
            txtTcpPort.Text = FindResource("DefaultPort");

            cmbReturnLossFreq.SelectedIndex = 33;

            GenerateColmnsDataGridForInv();
            tagdb = new TagDB();
            tagdbTmp = new TagDB();
            dgvInventoryTagResults.DataSource = tagdb.TagList;
            GenerateColmnsDataGridForTagOp();

            initTagOperationUI();
            initTagSelectUI();
            initDgvTagMask();


            if (ncdb == null)
                ncdb = new NetCardDB();

            cmbbxNetCard.DataSource = null;
            cmbbxNetCard.DataSource = ncdb.NetCardList;


            initDgvNetPort();
            initDgvNetPortUI();

            rb_fast_inv.Visible = false;
            cmbBaudrate.SelectedIndex = 1; //115200

            groupBox23.Enabled = false;

            cbbTestModel.SelectedIndex = 0;

            flowLayoutPanel5.Visible = false;
            flowLayoutPanel1.Height += 125;
            groupBox26.Height += 100;
            panel14.Visible = false;

            InitAntSequence();
        }

        private void R2000UartDemo_FormClosing(object sender, FormClosingEventArgs e)
        {
            closeLog();

            if (Inventorying)
            {
                btnInventory_Click_1(null, null);
            }
            ckDisplayLog.Checked = false;
        }

        private void tabCtrMain_SelectedIndexChanged(object sender, EventArgs e)
        {

            if (m_bLockTab)
            {
                tabCtrMain.SelectTab(1);
            }

            if(null != reader)
            {
                if (!FreqRegionFlag)
                {
                    reader.GetFrequencyRegion();
                    Thread.Sleep(1);
                }
            }

        }

#region Init
        private void initTagSelectUI()
        {
            combo_mast_id.SelectedIndex = 0;
            combo_menbank.SelectedIndex = 1;
            combo_action.SelectedIndex = 0;
            foreach (SessionID s in Enum.GetValues(typeof(SessionID)))
            {
                cmbbxSessionId.Items.Add(s);
            }
            cmbbxSessionId.SelectedIndex = cmbbxSessionId.Items.IndexOf(SessionID.S0);
            combo_mast_id.SelectedIndex = 0;
        }

        private void initTagOperationUI()
        {
            //read multibank
            foreach (Session s in Enum.GetValues(typeof(Session)))
            {
                cmbbxReadTagSession.Items.Add(s);
            }
            cmbbxReadTagSession.SelectedIndex = cmbbxReadTagSession.Items.IndexOf(Session.S0);
            foreach (Target s in Enum.GetValues(typeof(Target)))
            {
                cmbbxReadTagTarget.Items.Add(s);
            }
            cmbbxReadTagTarget.SelectedIndex = cmbbxReadTagTarget.Items.IndexOf(Target.A);
            foreach (ReadMode s in Enum.GetValues(typeof(ReadMode)))
            {
                cmbbxReadTagReadMode.Items.Add(s);
            }
            cmbbxReadTagReadMode.SelectedIndex = cmbbxReadTagReadMode.Items.IndexOf(ReadMode.MultiTagBySession);
            txtbxReadTagResAddr.Text = string.Format("{0}", 0);
            txtbxReadTagResCnt.Text = string.Format("{0}", 0);
            txtbxReadTagTidAddr.Text = string.Format("{0}", 0);
            txtbxReadTagTidCnt.Text = string.Format("{0}", 0);
            txtbxReadTagUserAddr.Text = string.Format("{0}", 0);
            txtbxReadTagUserCnt.Text = string.Format("{0}", 0);
            //sensortag
            chkbxReadSensorTag.Checked = false;
            radio_btn_johar_1.Checked = true;

            chkbxReadSensorTag.Checked = false;
            chkbxReadSensorTag_CheckedChanged(null, null);
            chkbxReadTagMultiBankEn.Checked = false;
            chkbxReadTagMultiBankEn_CheckedChanged(null, null);
        }

        private void initRealInvAnts()
        {
            antLists = new List<string>();
            antLists.Add(string.Format("{0}{1}", FindResource("Antenna"), 1));
            combo_realtime_inv_ants.Items.AddRange(antLists.ToArray());
        }

        private void initSaveLog()
        {
            if (!saveLog())
            {
                chkbxSaveLog.Checked = false;
                return;
            }
            inventory_times = 1;
        }
        
        private void initDgvTagMask()
        {
            dgvTagMask.AutoGenerateColumns = false;
            dgvTagMask.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.None;
            dgvTagMask.BackgroundColor = Color.White;

            tagMask_MaskNoColumn.DataPropertyName = "MaskID";
            tagMask_MaskNoColumn.HeaderText = FindResource("tagmask_MaskNo");
            tagMask_MaskNoColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.ColumnHeader;

            tagMask_SessionIdColumn.DataPropertyName = "Target";
            tagMask_SessionIdColumn.HeaderText = FindResource("tagmask_SessionID");
            tagMask_SessionIdColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.ColumnHeader;

            tagMask_ActionColumn.DataPropertyName = "ActionStr";
            tagMask_ActionColumn.HeaderText = FindResource("tagmask_Action");
            tagMask_ActionColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.ColumnHeader;

            tagMask_MembankColumn.DataPropertyName = "Bank";
            tagMask_MembankColumn.HeaderText = FindResource("tagmask_MemBank");
            tagMask_MembankColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.ColumnHeader;

            tagMask_StartAddrColumn.DataPropertyName = "StartAddrHexStr";
            tagMask_StartAddrColumn.HeaderText = FindResource("tagmask_StartAddr");
            tagMask_StartAddrColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.ColumnHeader;

            tagMask_MaskLenColumn.DataPropertyName = "MaskBitLenHexStr";
            tagMask_MaskLenColumn.HeaderText = FindResource("tagmask_MaskLen");
            tagMask_MaskLenColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.ColumnHeader;

            tagMask_MaskValueColumn.DataPropertyName = "Mask";
            tagMask_MaskValueColumn.HeaderText = FindResource("tagmask_MaskValue");
            tagMask_MaskValueColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.NotSet;
            tagMask_MaskValueColumn.MinimumWidth = 240;

            tagMask_TruncateColumn.DataPropertyName = "Truncate";
            tagMask_TruncateColumn.HeaderText = FindResource("tagmask_Truncate");
            tagMask_TruncateColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.NotSet;
            tagMask_TruncateColumn.Visible = false;

            combo_mast_id_Clear.SelectedIndex = 0;

            if (tagMaskDB == null)
                tagMaskDB = new TagMaskDB();
            dgvTagMask.DataSource = null;
            dgvTagMask.DataSource = tagMaskDB.TagList;

        }

        private void GenerateColmnsDataGridForInv()
        {
            dgvInventoryTagResults.AutoGenerateColumns = false;
            dgvInventoryTagResults.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.None;
            dgvInventoryTagResults.BackgroundColor = Color.White;

            SerialNumber_fast_inv.DataPropertyName = "SerialNumber";
            SerialNumber_fast_inv.HeaderText = "#";
            SerialNumber_fast_inv.AutoSizeMode = DataGridViewAutoSizeColumnMode.ColumnHeader;

            PC_fast_inv.DataPropertyName = "PC";
            PC_fast_inv.HeaderText = FindResource("PC");

            EPC_fast_inv.DataPropertyName = "EPC";
            EPC_fast_inv.HeaderText = FindResource("EPC");
            EPC_fast_inv.MinimumWidth = 240;

            ReadCount_fast_inv.DataPropertyName = "ReadCount";
            ReadCount_fast_inv.HeaderText = FindResource("ReadCount");
            ReadCount_fast_inv.AutoSizeMode = DataGridViewAutoSizeColumnMode.ColumnHeader;

            Rssi_fast_inv.DataPropertyName = "Rssi";
            Rssi_fast_inv.HeaderText = FindResource("Rssi");
            Rssi_fast_inv.AutoSizeMode = DataGridViewAutoSizeColumnMode.ColumnHeader;

            Freq_fast_inv.DataPropertyName = "Freq";
            Freq_fast_inv.HeaderText = FindResource("Freq");
            Freq_fast_inv.AutoSizeMode = DataGridViewAutoSizeColumnMode.ColumnHeader;

            Phase_fast_inv.DataPropertyName = "Phase";
            Phase_fast_inv.HeaderText = FindResource("Phase");
            Phase_fast_inv.Visible = false;
            Phase_fast_inv.AutoSizeMode = DataGridViewAutoSizeColumnMode.ColumnHeader;

            Antenna_fast_inv.DataPropertyName = "Antenna";
            Antenna_fast_inv.HeaderText = FindResource("Antenna");
            Antenna_fast_inv.AutoSizeMode = DataGridViewAutoSizeColumnMode.ColumnHeader;

            Data_fast_inv.DataPropertyName = "Data";
            Data_fast_inv.HeaderText = FindResource("Data");
            Data_fast_inv.MinimumWidth = 240;
            Data_fast_inv.AutoSizeMode = DataGridViewAutoSizeColumnMode.NotSet;
            Data_fast_inv.Visible = false;
        }
        
        private void GenerateColmnsDataGridForTagOp()
        {
            dgvTagOp.AutoGenerateColumns = false;
            dgvTagOp.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.None;
            dgvTagOp.BackgroundColor = Color.White;

            tagOp_SerialNumberColumn.DataPropertyName = "SerialNumber";
            tagOp_SerialNumberColumn.HeaderText = "#";
            tagOp_SerialNumberColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.ColumnHeader;

            tagOp_PcColumn.DataPropertyName = "PC";
            tagOp_PcColumn.HeaderText = FindResource("PC");

            tagOp_CrcColumn.DataPropertyName = "CRC";
            tagOp_CrcColumn.HeaderText = FindResource("CRC");

            tagOp_EpcColumn.DataPropertyName = "EPC";
            tagOp_EpcColumn.HeaderText = FindResource("EPC");
            tagOp_EpcColumn.MinimumWidth = 240;

            tagOp_OpCountColumn.DataPropertyName = "ReadCount";
            tagOp_OpCountColumn.HeaderText = FindResource("ReadCount");
            tagOp_OpCountColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.ColumnHeader;

            tagOp_DataColumn.DataPropertyName = "Data";
            tagOp_DataColumn.HeaderText = FindResource("Data");
            tagOp_DataColumn.MinimumWidth = 240;

            tagOp_DataLenColumn.DataPropertyName = "DataLen";
            tagOp_DataLenColumn.HeaderText = FindResource("DataLen");
            tagOp_DataLenColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.ColumnHeader;

            tagOp_AntennaColumn.DataPropertyName = "Antenna";
            tagOp_AntennaColumn.HeaderText = FindResource("Antenna");
            tagOp_AntennaColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.ColumnHeader;

            tagOp_FreqColumn.DataPropertyName = "Freq";
            tagOp_FreqColumn.HeaderText = FindResource("Freq");
            tagOp_FreqColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.ColumnHeader;

            tagOp_TemperatureColumn.DataPropertyName = "Temperature";
            tagOp_TemperatureColumn.HeaderText = FindResource("Temperature");
            tagOp_TemperatureColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.ColumnHeader;

            if (tagOpDb == null)
            {
                tagOpDb = new TagDB();
                dgvTagOp.DataSource = tagOpDb.TagList;
            }
        }

        private void InitAntSequence()
        {
            cmbAntSelect1.SelectedIndex = 0;
            cmbAntSelect2.SelectedIndex = 1;
            cmbAntSelect3.SelectedIndex = 2;
            cmbAntSelect4.SelectedIndex = 3;
            cmbAntSelect5.SelectedIndex = 4;
            cmbAntSelect6.SelectedIndex = 5;
            cmbAntSelect7.SelectedIndex = 6;
            cmbAntSelect8.SelectedIndex = 7;
        }

        private void bindInvAntTableEvents()
        {
            foreach (CheckBox cb in fast_inv_ants)
            {
                cb.CheckedChanged += new EventHandler(fastInvAntChecked);
            }
        }

#endregion Init





#region btnXxx
        private void btnConnect_Click(object sender, EventArgs e)
        {
            string tag = string.Empty;
            string arg1 = string.Empty; 
            int arg2 = 0;

            try
            {
                tag = "btnConnect_Click";
                if (rb_E710.Checked)
                {
                    ModelFlag = 2;
                }

                if (rb_R2000.Checked)
                {
                    ModelFlag = 1;
                }

                if(0 == ModelFlag)
                {
                    MessageBox.Show("请选择使用的模块类型");
                    return;
                }

                if (btnConnect.Text.Equals(FindResource("Connect")))
                {
                    if (radio_btn_rs232.Checked) 
                    {
                        readerType = ReaderType.SERIAL;  
                        arg1 = cmbComPort.Text.Trim();
                        arg2 = Convert.ToInt32(cmbBaudrate.Text);
                    }

                    if (radio_btn_tcp.Checked) 
                    {
                        readerType = ReaderType.TCP;
                        arg1 = ipIpServer.IpAddressStr;
                        arg2 = Convert.ToInt32(txtTcpPort.Text);
                    }

                    reader = Reader.Create(readerType, channels, arg1, arg2);
                    reader.MessageTransport += PrintTransportLog;
                    reader.MessageReadWhenInventory += Reader_MessageReadWhenInventory;
                    reader.ExceptionReceived += Reader_ExceptionReceived;
                    reader.FirmwareVersionCallback += ReshFirmwareVersion;
                    reader.FrequencyCallback += Reader_FrequencyCallback;
                    reader.SettingStatusCallback += Reader_SettingStatusCallback;
                    reader.AntPowerCallback += Reader_AntPowerCallback;
                    reader.TagOpResultCallback += Reader_TagOpResultCallback;
                    reader.ReaderIdentifierCallback += Reader_ReaderIdentifierCallback;
                    reader.ReaderTemperatureCallback += Reader_ReaderTemperatureCallback;
                    reader.GpioPinsCallback += Reader_GpioPinsCallback;
                    reader.WorkAntennaCallback += Reader_WorkAntennaCallback;
                    reader.RFPortReturnLossCallback += Reader_RFPortReturnLossCallback;
                    reader.RfLinkProfileCallback += Reader_RfLinkProfileCallback;
                    reader.ImpinjFastTidCallback += Reader_ImpinjFastTidCallback;
                    reader.E710ProfileCallback += Reader_E710ProfileCallback;
                    reader.AntConnectionDetectorCallback += Reader_AntConnectionDetectorCallback;
                    reader.SelectCallback += Reader_SelectCallback;
                    reader.QConfigCallback += Reader_QConfigCallback;
                    reader.EpcMatchCallback += Reader_EpcMatchCallback;
                    reader.Tm600ProfileCallback += Reader_Tm600ProfileCallback;
                    reader.E710SerialTestCallback += Reader_E710SerialTestCallback;
                    reader.FunctionIDCallback += Reader_FunctionIDCallback;
                    reader.AntSequenceCallback += Reader_AntSequenceCallback;
                    reader.MessageExceptionCalllback += Reader_MessageExceptionCalllback;
                    reader.Connect();

                    btnConnect.Text = FindResource("Disconnect");
                    grb_rs232.Enabled = false;
                    grbModuleBaudRate.Enabled = true;
                    string strLog = string.Format("{0} {1}@{2}", FindResource("tipConnect"), arg1, arg2);
                    RecordOpHistory(HistoryType.Normal, strLog);
                    SetFormEnable(true);
                }
                else if (btnConnect.Text.Equals(FindResource("Disconnect")))
                {
                    Inventorying = false;
                    isFastInv = false;
                    isBufferInv = false;
                    isRealInv = false;
                    doingFastInv = false;
                    doingRealInv = false;
                    doingBufferInv = false;
                    FreqRegionFlag = false;
                    CommunicateFlag = false;
                    setInvStoppedStatus();

                    if (radio_btn_rs232.Checked)
                    {
                        grb_rs232.Enabled = true;
                        grbModuleBaudRate.Enabled = false;
                    }
                    else if (radio_btn_tcp.Checked)
                    {
                        grb_tcp.Enabled = true;
                    }

                    SetFormEnable(false);
                    RecordOpHistory(HistoryType.Normal, string.Format("{0} {1}", FindResource("Disconnect"), reader.Name));
                    reader.MessageTransport -= PrintTransportLog;
                    reader.ExceptionReceived -= Reader_ExceptionReceived;
                    reader.FirmwareVersionCallback -= ReshFirmwareVersion;
                    reader.FrequencyCallback -= Reader_FrequencyCallback;
                    reader.SettingStatusCallback -= Reader_SettingStatusCallback;
                    reader.AntPowerCallback -= Reader_AntPowerCallback;
                    reader.TagOpResultCallback -= Reader_TagOpResultCallback;
                    reader.ReaderIdentifierCallback -= Reader_ReaderIdentifierCallback;
                    reader.ReaderTemperatureCallback -= Reader_ReaderTemperatureCallback;
                    reader.GpioPinsCallback -= Reader_GpioPinsCallback;
                    reader.WorkAntennaCallback -= Reader_WorkAntennaCallback;
                    reader.RFPortReturnLossCallback -= Reader_RFPortReturnLossCallback;
                    reader.RfLinkProfileCallback -= Reader_RfLinkProfileCallback;
                    reader.ImpinjFastTidCallback -= Reader_ImpinjFastTidCallback;
                    reader.E710ProfileCallback -= Reader_E710ProfileCallback;
                    reader.AntConnectionDetectorCallback -= Reader_AntConnectionDetectorCallback;
                    reader.SelectCallback -= Reader_SelectCallback;
                    reader.QConfigCallback -= Reader_QConfigCallback;
                    reader.EpcMatchCallback -= Reader_EpcMatchCallback;
                    reader.Tm600ProfileCallback -= Reader_Tm600ProfileCallback;
                    reader.E710SerialTestCallback -= Reader_E710SerialTestCallback;
                    reader.FunctionIDCallback -= Reader_FunctionIDCallback;
                    reader.AntSequenceCallback -= Reader_AntSequenceCallback;

                    reader.Disconnect();
                    reader = null;
                    btnConnect.Text = FindResource("Connect");
                    Thread.Sleep(5);
                }
            }
            catch (Exception ex)
            {
                reader = null;
                string strLog = string.Format("{0} {1}", FindResource("tipConnectFailedCause"), ex.Message);
                RecordOpHistory(HistoryType.Failed, strLog);
            }
        }

        private void Reader_MessageExceptionCalllback(object sender, MessageExceptionEventArgs e)
        {
            RecordOpHistory(HistoryType.Failed, e.ExMessage);
        }

        private void Reader_AntSequenceCallback(object sender, AntSequenceEventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate () 
            {
                string strCmdLog = "Antenna switch sequency :";
                WriteLog(lrtxtLog, strCmdLog, 0);
                if ((e.AntSequence[0] >= 0) && (e.AntSequence[0] <= 7))
                {
                    cmbAntSelect1.SelectedIndex = e.AntSequence[0];
                    txtAStay.Text = String.Format("{0}", e.AntSequence[1]);
                    strCmdLog = "Ant " + (e.AntSequence[0] + 1).ToString() + " inventory " + e.AntSequence[1].ToString() + " round";
                    WriteLog(lrtxtLog, strCmdLog, 0);
                }

                if ((e.AntSequence[2] >= 0) && (e.AntSequence[2] <= 7))
                {
                    cmbAntSelect2.SelectedIndex = e.AntSequence[2];
                    txtBStay.Text = String.Format("{0}", e.AntSequence[3]);
                    strCmdLog = "Ant " + (e.AntSequence[2] + 1).ToString() + " inventory " + e.AntSequence[3].ToString() + " round";
                    WriteLog(lrtxtLog, strCmdLog, 0);
                }

                if ((e.AntSequence[4] >= 0) && (e.AntSequence[4] <= 7))
                {
                    cmbAntSelect3.SelectedIndex = e.AntSequence[4];
                    txtCStay.Text = String.Format("{0}", e.AntSequence[5]);
                    strCmdLog = "Ant " + (e.AntSequence[4] + 1).ToString() + " inventory " + e.AntSequence[5].ToString() + " round";
                    WriteLog(lrtxtLog, strCmdLog, 0);
                }

                if ((e.AntSequence[6] >= 0) && (e.AntSequence[6] <= 7))
                {
                    cmbAntSelect4.SelectedIndex = e.AntSequence[6];
                    txtDStay.Text = String.Format("{0}", e.AntSequence[7]);
                    strCmdLog = "Ant " + (e.AntSequence[6] + 1).ToString() + " inventory " + e.AntSequence[7].ToString() + " round";
                    WriteLog(lrtxtLog, strCmdLog, 0);
                }

                if (e.AntSequence.Length > 9)
                {
                    if ((e.AntSequence[8] >= 0) && (e.AntSequence[8] <= 7))
                    {
                        cmbAntSelect5.SelectedIndex = e.AntSequence[8];
                        txtEStay.Text = String.Format("{0}", e.AntSequence[9]);
                        strCmdLog = "Ant " + (e.AntSequence[8] + 1).ToString() + " inventory " + e.AntSequence[9].ToString() + " 次";
                        WriteLog(lrtxtLog, strCmdLog, 0);
                    }

                    if ((e.AntSequence[10] >= 0) && (e.AntSequence[10] <= 7))
                    {
                        cmbAntSelect6.SelectedIndex = e.AntSequence[10];
                        txtFStay.Text = String.Format("{0}", e.AntSequence[11]);
                        strCmdLog = "Ant " + (e.AntSequence[10] + 1).ToString() + " inventory " + e.AntSequence[11].ToString() + " 次";
                        WriteLog(lrtxtLog, strCmdLog, 0);
                    }
                    if ((e.AntSequence[12] >= 0) && (e.AntSequence[12] <= 7))
                    {
                        cmbAntSelect7.SelectedIndex = e.AntSequence[12];
                        txtGStay.Text = String.Format("{0}", e.AntSequence[13]);
                        strCmdLog = "Ant " + (e.AntSequence[12] + 1).ToString() + " inventory " + e.AntSequence[13].ToString() + " 次";
                        WriteLog(lrtxtLog, strCmdLog, 0);
                    }

                    if ((e.AntSequence[14] >= 0) && (e.AntSequence[14] <= 7))
                    {
                        cmbAntSelect8.SelectedIndex = e.AntSequence[14];
                        txtHStay.Text = String.Format("{0}", e.AntSequence[15]);
                        strCmdLog = "Ant " + (e.AntSequence[14] + 1).ToString() + " inventory " + e.AntSequence[15].ToString() + " 次";
                        WriteLog(lrtxtLog, strCmdLog, 0);
                    }

                    tb_Interval.Text = String.Format("{0}", e.AntSequence[16]);
                    strCmdLog = "天线间延时: " + e.AntSequence[16].ToString() + " ms";
                    WriteLog(lrtxtLog, strCmdLog, 0);
                }
                else
                {
                    tb_Interval.Text = String.Format("{0}", e.AntSequence[8]);
                    strCmdLog = "天线间延时: " + e.AntSequence[8].ToString() + " ms";
                    WriteLog(lrtxtLog, strCmdLog, 0);
                }
            }));
        }

        private void Reader_FunctionIDCallback(object sender, GetFunctionIDEventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                cbb_FunctionId.SelectedIndex = e.FunctionID;
                string strCmdInfo = "Current function ID(HEX)：" + string.Format(" {0:X2}", e.FunctionID);
                WriteLog(lrtxtLog, strCmdInfo, 0);
            }));
        }

        private byte[] TestData;
        private int GtestRecCnt = 0;

        private void Reader_E710SerialTestCallback(object sender, E710SerialTestEventArgs e)
        {
            DelayTimeCmd.Stop();
            StartTestFlag = true;
            if(e.serialTest.Len == 1)
            {
                if(e.serialTest.Status == 0x10)
                {
                    BeginInvoke(new ThreadStart(delegate ()
                    {
                        btnSerialTest.Text = "Testing";
                        btnSerialTest.Enabled = false;
                        reader.E710SerailTestCmd(Gopid, Gtestcnt, TestData, TestData.Length);
                        startCmdTime = DateTime.Now;
                        DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, "接收到启动测试应答：Gtestcnt = {0}", Gtestcnt);
                        if (null != E710CmdTimer)
                        {
                            E710CmdTimer.Start();
                        } 
                        if (Gopid > 1) 
                        {
                            DelayTimeCmd.Start();
                        }
                        lbPCSendCnt.Text = String.Format("{0}", Gtestcnt + 1);
                    }));
                }
            }
            else
            {
                if(e.serialTest.Opid > 0x05)
                {
                    BeginInvoke(new ThreadStart(delegate ()
                    {
                        btnSerialTest.Text = "启动测试";
                        btnSerialTest.Enabled = true;
                        lbModelRevCnt.Text = String.Format("{0}", e.serialTest.RecCount);
                        lbModelSendCnt.Text = String.Format("{0}", e.serialTest.SendCount);
                        lbModelTestTimeCnt.Text = String.Format("{0}", e.serialTest.TestTime);
                        if (E710CmdTimer != null)
                        {
                            E710CmdTimer.Stop();
                            E710CmdTimer = null;
                        }
                        if(Gtestcnt >= Grepeat) 
                        {
                            TimeSpan span1 = DateTime.Now - startCmdTime;
                            long ts1 = span1.Hours * 60 * 60 * 1000 + span1.Minutes * 60 * 1000 + span1.Seconds * 1000 + span1.Milliseconds;
                            lbPCTestTimeCnt.Text = String.Format("{0}", ts1);
                            lbPCSendCnt.Text = String.Format("{0}", Grepeat);
                            return;
                        }
                        TimeSpan span = DateTime.Now - startCmdTime;
                        long ts = span.Hours * 60 * 60 * 1000 + span.Minutes * 60 * 1000 + span.Seconds * 1000 + span.Milliseconds;
                        lbPCTestTimeCnt.Text = String.Format("{0}", ts);
                        lbPCSendCnt.Text = String.Format("{0}", Gtestcnt + 1);
                        DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, "接收到80应答：Gtestcnt = {0}", Gtestcnt);
                    }));
                }
                else
                {
                    BeginInvoke(new ThreadStart(delegate ()
                    {
                        if(Gtestcnt >= Grepeat)
                        {
                            return;
                        }
                        else
                        {
                            GtestRecCnt++;
                            lbPCRecCnt.Text = String.Format("{0}", GtestRecCnt);
                            Gtestcnt++;
                            if(Gtestcnt >= Grepeat)
                            {
                                TimeSpan span1 = DateTime.Now - startCmdTime;
                                long ts1 = span1.Hours * 60 * 60 * 1000 + span1.Minutes * 60 * 1000 + span1.Seconds * 1000 + span1.Milliseconds;
                                lbPCTestTimeCnt.Text = String.Format("{0}", ts1);
                                lbPCSendCnt.Text = String.Format("{0}", Grepeat);
                                return;
                            }
                            TimeSpan span = DateTime.Now - startCmdTime;
                            long ts = span.Hours * 60 * 60 * 1000 + span.Minutes * 60 * 1000 + span.Seconds * 1000 + span.Milliseconds;
                            lbPCTestTimeCnt.Text = String.Format("{0}", ts);
                            reader.E710SerailTestCmd(Gopid, Gtestcnt, TestData, TestData.Length);
                            DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, "接收到00应答：Gtestcnt = {0}", Gtestcnt);
                            DelayTimeCmd.Start();
                            lbPCSendCnt.Text = String.Format("{0}", Gtestcnt + 1);
                        }
                    }));
                }
            }
        }

        private void Reader_Tm600ProfileCallback(object sender, Tm600ProfileEventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                CommunicateFlag = true;
                cbbTm600RFLink.SelectedIndex = e.Tm600Profile;
            }));
        }

        private void Reader_EpcMatchCallback(object sender, EpcMatchEventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                if (e.epcMatch.Match)
                {
                    txtAccessEpcMatch.Text = string.Format("{0}", ByteUtils.ToHex(e.epcMatch.Epc, "", " "));
                    RecordOpHistory(HistoryType.Success, string.Format("{0} {1}", FindResource("GetAccessEpcMatch"), string.Format("({0}){1}",
                        e.epcMatch.EpcLen, ByteUtils.ToHex(e.epcMatch.Epc, "", " "))));
                }
                else
                {

                }
            }));

        }

        private void Reader_QConfigCallback(object sender, QConfigEventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                CommunicateFlag = true;
                if (e.config.UseAdvanceConfig)
                {
                    rbDyQ.Checked = true;
                    cbbInitQValue.SelectedIndex = e.config.QInit;
                    cbbMinQValue.SelectedIndex = e.config.QMin;
                    cbbMaxQValue.SelectedIndex = e.config.QMax;
                    tbNumMinQ.Text = string.Format("{0}", e.config.NumMinQCycles);
                    tbMaxQSince.Text = String.Format("{0}", e.config.MaxQuerySinceEPC);
                }
                else
                {
                    rbStQ.Checked = true;
                    cbbInitQValue.SelectedIndex = e.config.QInit;
                    cbbMinQValue.SelectedIndex = e.config.QMin;
                    cbbMaxQValue.SelectedIndex = e.config.QMax;
                }
            }));

        }

        private void Reader_SelectCallback(object sender, SelectEventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                CommunicateFlag = true;
                string strResults = "";
                tagMaskDB.Clear();
                foreach (Select select in e.selects)
                {
                    strResults = string.Format("{0}\r\n{1};", strResults, select.ToString());
                    tagMaskDB.Add(select);
                }
            }));
        }

        private void Reader_AntConnectionDetectorCallback(object sender, AntConnectionDetectorEventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                CommunicateFlag = true;
                tbAntDectector.Text = string.Format("{0}", e.AntConnectionDetector);
            }));
        }

        private void Reader_E710ProfileCallback(object sender, E710ProfileEventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                CommunicateFlag = true;
                if(e.E710Profile.ProfileId > 4)
                {
                    string strlog = "The preset value is out of range, please reset";
                    RecordOpHistory(HistoryType.Failed, strlog);
                    return;
                }
                cbbE710RfLink.SelectedIndex = e.E710Profile.ProfileId;
                cbDrmSwich.Checked = e.E710Profile.UseDrmMode;
            }));
        }

        private void Reader_ImpinjFastTidCallback(object sender, ImpinjFastTidEventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                CommunicateFlag = true;
                if (e.ImpinjFastTid)
                {
                    rdbMonzaOn.Checked = true;
                }
                else
                {
                    rdbMonzaOff.Checked = true;
                }
            }));
        }

        private void Reader_RfLinkProfileCallback(object sender, RfLinkProfileEventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                CommunicateFlag = true;
                cmbModuleLink.SelectedIndex = e.RfLinkProfile;
            }));
        }

        private void Reader_RFPortReturnLossCallback(object sender, RfPortReturnLossEventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                CommunicateFlag = true;
                textReturnLoss.Text = string.Format("{0}", e.Loss);
            }));
        }

        private void Reader_WorkAntennaCallback(object sender, WorkAntennaEventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                CommunicateFlag = true;
                if (cmbWorkAnt.Items.Count < (int)(e.ant))
                {
                    MessageBox.Show(string.Format("Antenna not included: {0}", e.ant));
                    return;
                }
                cmbWorkAnt.SelectedIndex = (int)e.ant;

                if (cmbbxTagOpWorkAnt.Items.Count < (int)e.ant)
                {
                    MessageBox.Show(string.Format("Antenna not included: {0}", e.ant));
                    return;
                }

                cmbbxTagOpWorkAnt.SelectedIndex = (int)e.ant;

                if (MulAntReadTag)
                {
                    MulAntTag = (int)e.ant;
                }

            }));
        }

        private void Reader_GpioPinsCallback(object sender, GpioPinsEventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                CommunicateFlag = true;
                foreach (GpioPin gpi in e.gpios)
                {
                    if (gpi.ID == 1)
                    {
                        if (gpi.High)
                        {
                            rdbGpio1High.Checked = true;
                        }
                        else
                        {
                            rdbGpio1Low.Checked = true;
                        }
                    }
                    else if (gpi.ID == 2)
                    {
                        if (gpi.High)
                        {
                            rdbGpio2High.Checked = true;
                        }
                        else
                        {
                            rdbGpio2Low.Checked = true;
                        }
                    }
                }
            }));
        }

        private void Reader_ReaderTemperatureCallback(object sender, ReaderTemperatureEventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                CommunicateFlag = true;
                txtReaderTemperature.Text = string.Format("{0} ℃", e.ReaderTemperature);
            }));
        }

        private void Reader_ReaderIdentifierCallback(object sender, ReaderIdentifierEventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                CommunicateFlag = true;
                htbGetIdentifier.Text = e.ReaderIdentifier;
            }));

        }

        private void Reader_TagOpResultCallback(object sender, TagOpResultEventArgs e)
        {
            CommunicateFlag = true;
            UpdateTagResultsDgv(e.tagOps);
        }

        private void Reader_AntPowerCallback(object sender, AntPowerEventArgs e)
        {
            CommunicateFlag = true;
            BeginInvoke(new ThreadStart(delegate ()
            {                
                string strLog = "";
                for (int i = 0; i < (int)channels; i++)
                {
                    if (isTemppower && e.power[i] < 20)
                    {
                        txtbxOutputPows[i].Text = string.Format("{0}", 20);
                    }
                    else
                    {
                        txtbxOutputPows[i].Text = string.Format("{0}", e.power[i]);
                    }
                    strLog += string.Format("[{0},{1}] ", i + 1, e.power[i]);
                }
            }));
        }

        private void Reader_SettingStatusCallback(object sender, SettingEventArgs e)
        {
            CommunicateFlag = true;

            BeginInvoke(new ThreadStart(delegate () {
                string strlog = null;
                switch (e.cmd)
                {
                    case 0x69:
                        {
                            if (FactoryResetFlag)
                            {
                                if(e.status == ErrorCode.COMMAND_SUCCESS)
                                {
                                    strlog = "链路设置成功";
                                    RecordOpHistory(HistoryType.Failed, strlog);
                                    //天线端口功率（默认30）
                                    List<int> powList = new List<int>();
                                    for (int i = 0; i < (int)channels; i++)
                                    {
                                        powList.Add(30);
                                    }
                                    Thread.Sleep(500);
                                    reader.SetOutputPower(powList.ToArray());
                                    return;
                                }
                            }
                        }
                        break;
                    case 0x71:
                        if (e.status == ErrorCode.COMMAND_SUCCESS)
                        {
                            btnConnect_Click(null, null);
                        }
                        break;
                    case 0x74:
                        {
                            if (MulAntReadTag)
                            {
                                if (StopMulAntReadTag) return;
                                if(e.status == ErrorCode.COMMAND_SUCCESS)
                                {
                                    byte[] accessPwd = ByteUtils.FromHex(hexTb_accessPw.Text.Trim().Replace(" ", ""));
                                    if (chkbxReadTagMultiBankEn.Checked)
                                    {
                                        Session session = (Session)cmbbxReadTagSession.SelectedItem;
                                        Target target = (Target)cmbbxReadTagTarget.SelectedItem;
                                        int resAddr = Convert.ToInt32(txtbxReadTagResAddr.Text.Trim());
                                        int resLen = Convert.ToInt32(txtbxReadTagResCnt.Text.Trim());

                                        int tidAddr = Convert.ToInt32(txtbxReadTagTidAddr.Text.Trim());
                                        int tidLen = Convert.ToInt32(txtbxReadTagTidCnt.Text.Trim());
                                        int usrAddr = Convert.ToInt32(txtbxReadTagUserAddr.Text.Trim());
                                        int usrLen = Convert.ToInt32(txtbxReadTagUserCnt.Text.Trim());
                                        ReadMode readMode = (ReadMode)cmbbxReadTagReadMode.SelectedItem;
                                        int timeouts = 5;
                                        reader.Read(resAddr, resLen, tidAddr, tidLen, usrAddr, usrLen, accessPwd, session, target, readMode, timeouts);
                                    }
                                    else
                                    {
                                        MemBank memBank = GetMemBank();
                                        int startAddr = Convert.ToInt32(tb_startWord.Text.Trim());
                                        int readlen = Convert.ToInt32(tb_wordLen.Text.Trim());
                                        reader.Read(memBank, startAddr, readlen, accessPwd);
                                    }
                                }
                            }
                        }
                        break;
                    case 0x76:
                        {
                            if (FactoryResetFlag)
                            {
                                if(e.status == ErrorCode.COMMAND_SUCCESS)
                                {
                                    strlog = "功率设置成功";
                                    RecordOpHistory(HistoryType.Failed, strlog); 
                                    //设置波特率（默认115200)
                                    SetFormEnable(true);
                                    btnFactoryReset.Enabled = true;
                                    FactoryResetFlag = false;
                                    return;
                                }
                            }
                        }
                        break;
                    case 0x78:
                        {
                            if (FactoryResetFlag)
                            {
                                if(e.status == ErrorCode.COMMAND_SUCCESS)
                                {
                                    strlog = "频段设置成功";
                                    RecordOpHistory(HistoryType.Failed, strlog);

                                    //射频链路
                                    reader.SetRfLinkProfile(1);
                                    return;
                                }

                            }
                        }
                        break;
                    case 0x98:
                        if (readJoharEn)
                        {
                            if (e.status == ErrorCode.COMMAND_SUCCESS)
                            {
                                reader.ReadTagJohar();
                            }
                        }
                    	strlog = "No filter settings found";
                        break;
                    case 0x8C:
                        if (readJoharEn)
                        {
                            if (e.status == ErrorCode.COMMAND_SUCCESS)
                            {
                                fastIdEn = true;
                                reader.SelectJohar();
                            }
                        }
                        else
                        {
                            if (e.status == ErrorCode.COMMAND_SUCCESS)
                            {
                                fastIdEn = false;
                                reader.ClearSelect(SelectFunction.MaskAll);
                            }
                        }

                        break;


                }
                switch (e.status)
                {
                    case ErrorCode.NOMAL_MODE:
                        break;
                    case ErrorCode.COMMAND_FAIL:
                    	strlog = "Command failed";
                        break;
                    case ErrorCode.COMMAND_SUCCESS:
                    	strlog = "Command succeeded";
                        break;
                }
                RecordOpHistory(HistoryType.Failed, strlog);
            }));

        }

        private void Reader_FrequencyCallback(object sender, FreqEventArgs e)
        {
            CommunicateFlag = true;
            BeginInvoke(new ThreadStart(delegate ()
            {
                FreqRegionFlag = true;


                cmbFrequencyStart.SelectedIndex = -1;
                cmbFrequencyEnd.SelectedIndex = -1;

                rdbRegionFcc.Checked = false;
                rdbRegionEtsi.Checked = false;
                rdbRegionChn.Checked = false; 
                cbUserDefineFreq.Checked = false;

                textStartFreq.Text = "";
                TextFreqInterval.Text = "";
                textFreqQuantity.Text = "";


                FrequencyRegion frequencyRegion = e.FreqRegion;
                string starttmp = (frequencyRegion.StartFreq / 1000.00f).ToString("0.00");
                string endtmp = (frequencyRegion.EndFreq / 1000.00f).ToString("0.00");


                switch (frequencyRegion.Region)
                {
                    case RFID_API_ver1.Region.FCC:
                        rdbRegionFcc.Checked = true;
                        groupBox23.Enabled = false;
                        groupBox21.Enabled = true;
                        cmbFrequencyStart.SelectedIndex = cmbFrequencyStart.Items.IndexOf(starttmp);
                        cmbFrequencyEnd.SelectedIndex = cmbFrequencyEnd.Items.IndexOf(endtmp);
                        break;
                    case RFID_API_ver1.Region.ETSI:
                        rdbRegionEtsi.Checked = true;
                        groupBox23.Enabled = false;
                        groupBox21.Enabled = true;
                        cmbFrequencyStart.SelectedIndex = cmbFrequencyStart.Items.IndexOf(starttmp);
                        cmbFrequencyEnd.SelectedIndex = cmbFrequencyEnd.Items.IndexOf(endtmp);
                        break;
                    case RFID_API_ver1.Region.CHN:
                        rdbRegionChn.Checked = true;
                        groupBox23.Enabled = false;
                        groupBox21.Enabled = true;
                        cmbFrequencyStart.SelectedIndex = cmbFrequencyStart.Items.IndexOf(starttmp);
                        cmbFrequencyEnd.SelectedIndex = cmbFrequencyEnd.Items.IndexOf(endtmp);
                        break;
                    case RFID_API_ver1.Region.CUSTOMIZE:
                        cbUserDefineFreq.Checked = true;
                        groupBox23.Enabled = true;
                        groupBox21.Enabled = false;
                        textStartFreq.Text = string.Format("{0}", frequencyRegion.StartFreq);
                        TextFreqInterval.Text = string.Format("{0}", frequencyRegion.FreqStep);
                        textFreqQuantity.Text = string.Format("{0}", frequencyRegion.FreqQuantity);
                        break;
                    default:
                        break;
                }
            }));
        }

        private void btnGetFrequencyRegion_Click(object sender, EventArgs e)
        {
            try
            {
                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipGetFrequencyRegion")));
                reader.GetFrequencyRegion();
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnSetFrequencyRegion_Click(object sender, EventArgs e)
        {
            try
            {
                FrequencyRegion frequencyRegion = new FrequencyRegion();
                if (rdbRegionFcc.Checked == true)
                {
                    frequencyRegion.Region = RFID_API_ver1.Region.FCC;
                    frequencyRegion.StartFreq =(int) (float.Parse(cmbFrequencyStart.Text) * 1000);
                    frequencyRegion.EndFreq = (int)(float.Parse(cmbFrequencyEnd.Text) * 1000);
                }
                else if (rdbRegionEtsi.Checked == true)
                {
                    frequencyRegion.Region = RFID_API_ver1.Region.ETSI;
                    frequencyRegion.StartFreq = (int)(float.Parse(cmbFrequencyStart.Text) * 1000);
                    frequencyRegion.EndFreq = (int)(float.Parse(cmbFrequencyEnd.Text) * 1000);
                }
                else if (rdbRegionChn.Checked == true)
                {
                    frequencyRegion.Region = RFID_API_ver1.Region.CHN;
                    frequencyRegion.StartFreq = (int)(float.Parse(cmbFrequencyStart.Text) * 1000);
                    frequencyRegion.EndFreq = (int)(float.Parse(cmbFrequencyEnd.Text) * 1000);
                }
                else if (cbUserDefineFreq.Checked == true)
                {
                    frequencyRegion.Region = RFID_API_ver1.Region.CUSTOMIZE;
                    frequencyRegion.StartFreq = Convert.ToInt32(textStartFreq.Text.Trim());
                    if(frequencyRegion.StartFreq > 928000 || frequencyRegion.StartFreq < 865000)
                    {
                        MessageBox.Show("The frequency range is incorrect, please fill in again");
                        return;
                    }
                    frequencyRegion.FreqStep = Convert.ToInt32(TextFreqInterval.Text.Trim());
                    frequencyRegion.FreqQuantity = Convert.ToInt32(textFreqQuantity.Text.Trim());
                    frequencyRegion.EndFreq = frequencyRegion.StartFreq + frequencyRegion.FreqStep * frequencyRegion.FreqQuantity;
                    if(frequencyRegion.EndFreq > 928000 || frequencyRegion.EndFreq < 865000 || frequencyRegion.EndFreq < frequencyRegion.StartFreq)
                    {
                        MessageBox.Show("The frequency range is incorrect, please fill in again");
                        return;
                    }
                }
                RecordOpHistory(HistoryType.Normal, string.Format("{0} {1}", FindResource("tipSetFrequencyRegion"), frequencyRegion));
                reader.SetFrequencyRegion(frequencyRegion);
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnSetBeeperMode_Click(object sender, EventArgs e)
        {
            try
            {
                BeeperMode mode = BeeperMode.Quiet;
                switch (cbbBeepStatus.SelectedIndex)
                {
                    case 0:
                        mode = BeeperMode.Quiet;
                        break;
                    case 1:
                        mode = BeeperMode.EveryInventory;
                        break;
                    case 2:
                        mode = BeeperMode.EveryReadTag;
                        break;
                    default:
                        MessageBox.Show(string.Format("{0}", FindResource("SelectBeeperBehavior")));
                        return;
                }
                RecordOpHistory(HistoryType.Normal, string.Format("{0} {1}", FindResource("SetBeeperMode"), mode));
                reader.SetBeeperMode(mode);
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnReadGpioValue_Click(object sender, EventArgs e)
        {
            try
            {
                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("ReadGpioValue")));
                reader.ReadGpioValue();
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnWriteGpio3Value_Click(object sender, EventArgs e)
        {
            try
            {
                GpioPin gpo = new GpioPin(3, false);
                if (rdbGpio3High.Checked == true)
                {
                    gpo.High = true;
                }
                else if (rdbGpio3Low.Checked == true)
                {
                    gpo.High = false;
                }
                else
                {
                    MessageBox.Show(string.Format("{0}", FindResource("SelectGPOValue")));
                    return;
                }
                RecordOpHistory(HistoryType.Normal, string.Format("{0} {1}", FindResource("WriteGpioValue"), gpo));
                reader.WriteGpioValue(gpo);
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnWriteGpio4Value_Click(object sender, EventArgs e)
        {
            try
            {
                GpioPin gpo = new GpioPin(4, false);
                if (rdbGpio4High.Checked == true)
                {
                    gpo.High = true;
                }
                else if (rdbGpio4Low.Checked == true)
                {
                    gpo.High = false;
                }
                else
                {
                    MessageBox.Show(string.Format("{0}", FindResource("SelectGPOValue")));
                    return;
                }
                RecordOpHistory(HistoryType.Normal, string.Format("{0} {1}", FindResource("WriteGpioValue"), gpo.ToString()));
                reader.WriteGpioValue(gpo);
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnGetAntDetector_Click(object sender, EventArgs e)
        {
            try
            {
                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipGetAntDetector")));
                reader.GetAntConnectionDetector();
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnSetAntDetector_Click(object sender, EventArgs e)
        {
            try
            {
                int sensitivity = Convert.ToInt32(tbAntDectector.Text.Trim());
                RecordOpHistory(HistoryType.Normal, string.Format("{0} {1}", FindResource("tipSetAntDetector"), sensitivity));
                reader.SetAntConnectionDetector(sensitivity);
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnResetReader_Click(object sender, EventArgs e)
        {
            try
            {
                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("ResetReader")));
                reader.Reset();

                //RecordOpResultsHistory(string.Format("{0}", FindResource("ResetReader")), errorCode);
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnSetReadAddress_Click(object sender, EventArgs e)
        {
            try
            {
                if(htxtReadId.Text.Trim().Length < 1) 
                {
                    MessageBox.Show(string.Format("{0}", FindResource("tipValueIsNotNull")));
                    return;
                }

                int addr = Convert.ToInt32(htxtReadId.Text.Trim());
                RecordOpHistory(HistoryType.Normal, string.Format("{0} {1}", FindResource("SetReaderAddress"), addr));
                reader.SetReaderAddress(addr);
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnGetFirmwareVersion_Click(object sender, EventArgs e)
        {
            try
            {
                txtFirmwareVersion.Text = "";
                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipGetFirmwareVersion")));
                reader.GetFirmwareVersion();

            }
            catch (Exception ex)
            {
                OnLog(ex);
            }

        }

        private void ReshFirmwareVersion(object sender, FirmwareVersionEventArgs args) 
        {              

            BeginInvoke(new ThreadStart(delegate ()
            {
                CommunicateFlag = true;
                string fwVer = string.Format("{0:x2}.{1:x2}", args.Info.Major, args.Info.Minor);
                txtFirmwareVersion.Text = fwVer;
                RecordOpHistory(HistoryType.Normal, string.Format("chip type：{0}", args.Info.Chip));
            }));
        }




        private void btnSetUartBaudrate_Click(object sender, EventArgs e)
        {
            try
            {
                if (cmbSetBaudrate.SelectedItem == null)
                {
                    MessageBox.Show(string.Format("{0}", FindResource("tipBaudrateIsNotNull")));
                    return;
                }
                RecordOpHistory(HistoryType.Normal, string.Format("{0} {1}", FindResource("tipSetUartBaudrate"), cmbSetBaudrate.SelectedItem));
                reader.SetUartBaudrate(Convert.ToInt32(cmbSetBaudrate.SelectedItem));
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnGetReaderTemperature_Click(object sender, EventArgs e)
        {
            try
            {
                txtReaderTemperature.Text = "";
                reader.GetReaderTemperature();
                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipGetReaderTemperature")));
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnGetOutputPower_Click(object sender, EventArgs e)
        {
            Console.WriteLine("BtnGetPower_Click");
            try
            {
                foreach (TextBox tb in txtbxOutputPows)
                {
                    tb.Text = "";
                }
                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipGetOutputPower")));
                reader.GetOutputPower((int)channels == 16 ? true : false);
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnSetOutputPower_Click(object sender, EventArgs e)
        {
            Console.WriteLine("BtnSetPower_Click");
            try
            {
                string strLog = "";
                List<int> powList = new List<int>();
                for (int i = 0; i < txtbxOutputPows.Length; i++)
                {
                    if (txtbxOutputPows[i].Enabled == true)
                    {
                        strLog += string.Format("[{0},{1}] ", i + 1, txtbxOutputPows[i].Text.Trim());
                        powList.Add(Convert.ToInt32(txtbxOutputPows[i].Text.Trim()));
                    }
                }
                RecordOpHistory(HistoryType.Normal, string.Format("{0} {1}", FindResource("tipSetOutputPower"), strLog));
                reader.SetOutputPower(powList.ToArray());
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnGetWorkAntenna_Click(object sender, EventArgs e)
        {
            try
            {
                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("GetWorkAntenna")));
                reader.GetWorkAntenna();
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnSetWorkAntenna_Click(object sender, EventArgs e)
        {
            try
            {
                if (cmbWorkAnt.SelectedItem == null)
                {
                    MessageBox.Show(string.Format("{0}", FindResource("SelectAntenna")));
                    return;
                }
                Antenna antenna = (Antenna)cmbWorkAnt.SelectedIndex;
                RecordOpHistory(HistoryType.Normal, string.Format("{0} {1}", FindResource("SetWorkAntenna"), antenna));
                reader.SetWorkAntenna(antenna);
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnGetAccessEpcMatch_Click(object sender, EventArgs e)
        {
            try
            {
                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipGetAccessEpcMatch")));
                txtAccessEpcMatch.Text = "";
                reader.GetAccessEpcMatch();
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnSetAccessEpcMatch_Click(object sender, EventArgs e)
        {
            try
            {
                if (cmbSetAccessEpcMatch.Text.Trim().Equals(""))
                {
                    MessageBox.Show(FindResource("tipHaveNotYetSelectedTag"));
                    return;
                }
                string strMacth = string.Format("{0}", cmbSetAccessEpcMatch.Text.Trim().Replace(" ", ""));
                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipSetAccessEpcMatch")));
                txtAccessEpcMatch.Text = cmbSetAccessEpcMatch.Text;
                reader.SetAccessEpcMatch(new EpcMatch(true, ByteUtils.FromHex(strMacth.Trim().Replace(" ", ""))));
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnCancelAccessEpcMatch_Click(object sender, EventArgs e)
        {
            try
            {
                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("CancelAccessEpcMatch")));
                reader.SetAccessEpcMatch(new EpcMatch(false, null));
                txtAccessEpcMatch.Text = "";
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private bool StopMulAntReadTag = true;
        private int RefreshTagResult = 0;
        private void btnReadTag_Click(object sender, EventArgs e)
        {
            try
            {
                if (btnReadTag.Text.Equals(FindResource("Start")))
                {
                    btnReadTag.Text = "Stop";
                    StopMulAntReadTag = false;
                    RefreshTagResult = 1;
                }
                else if (btnReadTag.Text.Equals(FindResource("Stop")))
                {
                    btnReadTag.Text = "Start";
                    StopMulAntReadTag = true;
                    RefreshTagResult = 2;
                    return;
                }else if (btnReadTag.Text.Equals(FindResource("ReadTag")))
                {
                    RefreshTagResult = 0;
                    StopMulAntReadTag = true;
                }
                tagOpDb.Clear();
                tagOpDb.Repaint();

                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("ReadTag")));

                if (!ReaderUtils.CheckFourBytesPwd(hexTb_accessPw.Text))
                {
                    MessageBox.Show(string.Format("{0}", FindResource("tipWrongPassword")), string.Format("{0}", FindResource("ReadTag")));
                    return;
                }
                byte[] accessPwd = ByteUtils.FromHex(hexTb_accessPw.Text.Trim().Replace(" ", ""));

                TagOpResult[] tagOpResults = null;
                if (chkbxReadTagMultiBankEn.Checked == true)
                {
                    Session session = (Session)cmbbxReadTagSession.SelectedItem;
                    Target target = (Target)cmbbxReadTagTarget.SelectedItem;
                    int resAddr = Convert.ToInt32(txtbxReadTagResAddr.Text.Trim());
                    int resLen = Convert.ToInt32(txtbxReadTagResCnt.Text.Trim()); 

                    int tidAddr = Convert.ToInt32(txtbxReadTagTidAddr.Text.Trim());
                    int tidLen = Convert.ToInt32(txtbxReadTagTidCnt.Text.Trim());
                    int usrAddr = Convert.ToInt32(txtbxReadTagUserAddr.Text.Trim());
                    int usrLen = Convert.ToInt32(txtbxReadTagUserCnt.Text.Trim());
                    ReadMode readMode = (ReadMode)cmbbxReadTagReadMode.SelectedItem;
                    int timeouts = 5;
                    reader.Read(resAddr, resLen, tidAddr, tidLen, usrAddr, usrLen, accessPwd, session, target, readMode, timeouts);
                }
                else
                {
                    MemBank memBank = GetMemBank();
                    int startAddr = Convert.ToInt32(tb_startWord.Text.Trim());
                    int readlen = Convert.ToInt32(tb_wordLen.Text.Trim());
                    if (readlen == 0)
                    {
                        MessageBox.Show(string.Format("{0} (readLen > 0)", FindResource("tipLengthRange")), string.Format("{0}", FindResource("ReadTag")));
                        return;
                    }
                     reader.Read(memBank, startAddr, readlen, accessPwd);
                }
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnWriteTag_Click(object sender, EventArgs e)
        {
            try
            {
                RefreshTagResult = 0;
                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipWriteTag")));
                if (!ReaderUtils.CheckFourBytesPwd(hexTb_accessPw.Text))
                {
                    MessageBox.Show(string.Format("{0}", FindResource("tipWrongPassword")), string.Format("{0}", FindResource("tipWriteTag")));
                    return;
                }
                byte[] accessPwd = ByteUtils.FromHex(hexTb_accessPw.Text.Trim().Replace(" ", ""));

                string strData = hexTb_WriteData.Text.Trim().Replace(" ", "");
                if (!ReaderUtils.CheckIsNByteString(strData, 4))
                {
                    MessageBox.Show(string.Format("{0}", FindResource("tipWordStringFotmatError")));
                    return;
                }
                byte[] writeData = ByteUtils.FromHex(strData);

                MemBank memBank = GetMemBank();
                int startAddr = Convert.ToInt32(tb_startWord.Text.Trim());
                int writelen = Convert.ToInt32(tb_wordLen.Text.Trim());
                if (writelen == 0)
                {
                    MessageBox.Show(string.Format("{0} (writeLen > 0)", FindResource("tipLengthRange")), string.Format("{0}", FindResource("tipWriteTag")));
                    return;
                }

                TagOpResult[] tagOpResults = null;
                DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, "accessPwd={0}, writeData={1}", ByteUtils.ToHex(accessPwd, "", " "), ByteUtils.ToHex(writeData, "", " "));
                if (radio_btnBlockWrite.Checked == true)
                {
                    reader.BlockWrite(accessPwd, memBank, startAddr, writelen, writeData);
                }
                else
                {
                    reader.Write(accessPwd, memBank, startAddr, writelen, writeData);
                }
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnLockTag_Click(object sender, EventArgs e)
        {
            try
            {
                RefreshTagResult = 0;
                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipLockTag")));

                if (!ReaderUtils.CheckFourBytesPwd(hexTb_accessPw.Text))
                {
                    MessageBox.Show(string.Format("{0}", FindResource("tipWrongPassword")), string.Format("{0}", FindResource("tipLockTag")));
                    return;
                }
                byte[] accessPwd = ByteUtils.FromHex(hexTb_accessPw.Text.Trim().Replace(" ", ""));

                LockMemBank membank = GetLockBank();
                LockType lockType = GetLockType();
                reader.Lock(accessPwd, membank, lockType);
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnKillTag_Click(object sender, EventArgs e)
        {
            try
            {
                RefreshTagResult = 0;
                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipKillTag")));

                if (!ReaderUtils.CheckFourBytesPwd(htxtKillPwd.Text))
                {
                    MessageBox.Show(string.Format("{0}", FindResource("tipWrongPassword")), string.Format("{0}", FindResource("tipKillTag")));
                    return;
                }
                byte[] killPwd = ByteUtils.FromHex(htxtKillPwd.Text.Trim().Replace(" ", ""));
                reader.Kill(killPwd);
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private MemBank GetMemBank()
        {
            if (rdbEpc.Checked == true)
            {
                return MemBank.EPC;
            }
            else if (rdbReserved.Checked == true)
            {
                return MemBank.RESERVED;
            }
            else if (rdbTid.Checked == true)
            {
                return MemBank.TID;
            }
            else if (rdbUser.Checked == true)
            {
                return MemBank.USER;
            }
            else
            {
                throw new Exception("please select a MemBank parameter");
            }
        }

        private LockType GetLockType()
        {
            if (rdbFree.Checked == true)
            {
                return LockType.UNLOCK;
            }
            else if (rdbLock.Checked == true)
            {
                return LockType.LOCK;
            }
            else if (rdbFreeEver.Checked == true)
            {
                return LockType.PERMANENT_UNLOCK;
            }
            else if (rdbLockEver.Checked == true)
            {
                return LockType.PERMANENT_LOCK;
            }
            else
            {
                throw new Exception("please select a LockType parameter");
            }
        }

        private LockMemBank GetLockBank()
        {
            if (rdbUserMemory.Checked == true)
            {
                return LockMemBank.USER;
            }
            else if (rdbTidMemory.Checked == true)
            {
                return LockMemBank.TID;
            }
            else if (rdbEpcMermory.Checked == true)
            {
                return LockMemBank.EPC;
            }
            else if (rdbAccessPwd.Checked == true)
            {
                return LockMemBank.ACCESS_PASSWORD;
            }
            else if (rdbKillPwd.Checked == true)
            {
                return LockMemBank.KILL_PASSWORD;
            }
            else
            {
                throw new Exception("please select a LockMemBank parameter");
            }
        }

        private int TagJoharCnt = 0;
        private int MulTagCnt = 0;
        private void UpdateTagResultsDgv(TagOpResult[] tagOpResults)
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                lock (tagOpDb)
                {
                    if(RefreshTagResult == 0)
                    {
                        tagOpDb.Clear();
                        tagOpDb.Repaint();
                    }

                    if (tagOpResults != null)
                    {
                        string tmp = null;
                        HistoryType type = HistoryType.Failed;
                        foreach (TagOpResult top in tagOpResults)
                        {                            
                            //DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, string.Format("tagOpResults = {0}", top.OpResult));
                            switch (top.OpResult)
                            {                                 
                                case ErrorCode.TAG_INVENTORY_ERROR:
                                    tmp = "Error occurred during inventory";
                                    break;
                                case ErrorCode.TAG_READ_ERROR:
                                    tmp = "Error occurred during read";
                                    break;
                                case ErrorCode.TAG_WRITE_ERROR:
                                    tmp = "Error occurred during write";
                                    break;
                                case ErrorCode.TAG_LOCK_ERROR:
                                    tmp = "Error occurred during lock";
                                    break;
                                case ErrorCode.TAG_KILL_ERROR:
                                    tmp = "Error occurred during kill";
                                    break;
                                case ErrorCode.NO_TAG_ERROR:
                                    tmp = "There is no tag to be operated";
                                    break;
                                case ErrorCode.INVENTORY_OK_BUT_ACCESS_FAIL:
                                    tmp = "Tag Inventoried but access failed";
                                    break;
                                case ErrorCode.ACCESS_OR_PASSWORD_ERROR:
                                    tmp = "Access failed or wrong password";
                                    break;
                                case ErrorCode.PARAMETER_INVALID:
                                    tmp = "Invalid parameter";
                                    break;
                                case ErrorCode.PARAMETER_INVALID_WORDCNT_TOO_LONG:
                                    tmp = "WordCnt is too long";
                                    break;
                                case ErrorCode.PARAMETER_INVALID_MEMBANK_OUT_OF_RANGE:
                                    tmp = "MemBank out of range";
                                    break;
                                case ErrorCode.PARAMETER_INVALID_LOCK_REGION_OUT_OF_RANGE:
                                    tmp = "Lock region out of range";
                                    break;
                                case ErrorCode.PARAMETER_INVALID_LOCK_ACTION_OUT_OF_RANGE:
                                    tmp = "LockType out of range";
                                    break;
                                case ErrorCode.PARAMETER_EPC_MATCH_LEN_TOO_LONG:
                                    tmp = "EPC match is too long";
                                    break;
                                case ErrorCode.PARAMETER_EPC_MATCH_LEN_ERROR:
                                    tmp = "EPC match length wrong";
                                    break;
                                case ErrorCode.PARAMETER_INVALID_EPC_MATCH_MODE:
                                    tmp = "Invalid EPC match mode";
                                    break;
                                case ErrorCode.COMMAND_SUCCESS:
                                    tmp = "Command succeeded";
                                    type = HistoryType.Success;
                                    tagOpDb.Add(top.Tag);
                                    break;
                            }
                        }
                        RecordOpHistory(type, tmp);
                        if (readJoharEn)
                        {
                            int cnt = tagOpResults[0].TagCount;
                            DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, string.Format("cnt = {0}, tagOpResults = {1}", cnt, tagOpResults.Length));
                            if (cnt != tagOpResults.Length)
                            {
                                DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, string.Format("tagOpResults = {0}", TagJoharCnt));
                                if(cnt == TagJoharCnt)
                                {
                                    TagJoharCnt = 0;
                                    reader.ReadTagJohar();
                                    DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, string.Format("ReadTagJohar 1"));
                                }
                                TagJoharCnt += tagOpResults.Length;
                            }
                            else
                            {
                                TagJoharCnt = 0;
                                reader.ReadTagJohar();
                                DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, string.Format("ReadTagJohar 2"));
                            }
                        }

                        if (MulAntReadTag)
                        {
                            int cnt = tagOpResults[0].TagCount;
                            if(cnt != tagOpResults.Length)
                            {
                                if(cnt == MulTagCnt)
                                {
                                    MulTagCnt = 0;
                                    MulAntTag++;
                                    if (MulAntTag >= (int)channels) MulAntTag = 0;
                                    reader.SetWorkAntenna((Antenna)MulAntTag);
                                }
                                MulTagCnt += tagOpResults.Length;
                            }
                            else
                            {
                                MulTagCnt = 0;
                                MulAntTag++;
                                if (MulAntTag >= (int)channels) MulAntTag = 0;
                                reader.SetWorkAntenna((Antenna)MulAntTag);
                            }
                        }
                    }

                }
            }));

        }

        private void btnClearTagOpResult_Click(object sender, EventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                lock (tagOpDb)
                {
                    tagOpDb.Clear();
                    tagOpDb.Repaint();
                }

            }));
        }

        private void ParseRawMessage(RFMessage msg)
        {
            object obj = Enum.ToObject(typeof(CMD), msg.Command);
            bool defined = Enum.IsDefined(typeof(CMD), obj);
            RecordOpHistory(HistoryType.Normal, (defined ? string.Format("{0}", obj) : string.Format("{0:x2}", msg.Command)));
        }

        private void btnSendData_Click(object sender, EventArgs e)
        {
            try
            {
                string input = htxtSendData.Text.Trim().Replace(" ", "");
                if (!ReaderUtils.CheckIsNByteString(input, 2))
                {
                    throw new Exception(string.Format("{0}", FindResource("TipHexStringFotmatError")));
                }

                if (reader.IsInventorying())
                {
                    throw new Exception(string.Format("{0}", FindResource("Inventorying")));
                }
                string strRawData = string.Format("{0}{1}", input, htxtCheckData.Text);
                RFMessage msg = new RFMessage(ByteUtils.FromHex(strRawData));
                reader.SendRaw(msg);

                if (0xA0 == msg.Command || 0x8A == msg.Command)
                {
                    if (!FreqRegionFlag)
                    {
                        reader.GetFrequencyRegion();
                        Thread.Sleep(1);
                    }
                    dispatcherTimer.Start();
                    readratePerSecond.Start();
                    reader.TagRead += Reader_TagRead;
                    reader.CommandStatistics += Reader_CommandStatistics;

                    //if (msg.Data[0] == 0x04)
                    //{
                    //    dispatcherTimer.Start();
                    //    readratePerSecond.Start();
                    //    reader.TagRead += Reader_TagRead;
                    //    reader.CommandStatistics += Reader_CommandStatistics;
                    //}
                    //else
                    //{
                    //    dispatcherTimer.Stop();
                    //    readratePerSecond.Stop();
                    //    reader.TagRead -= Reader_TagRead;
                    //    reader.CommandStatistics -= Reader_CommandStatistics;
                    //}
                }
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnClearData_Click(object sender, EventArgs e)
        {
            string tag = string.Empty;
            try
            {
                tag = "btnClearData_Click";
                htxtSendData.Text = "";
                htxtCheckData.Text = "";
            }
            catch (Exception ex)
            {
                OnLog(tag, ex);
            }
        }

        private void btnSaveData_Click(object sender, EventArgs e)
        {
            string tag = string.Empty;
            try
            {
                tag = "btnSaveData_Click";
                string strLog = lrtxtDataTran.Text;
                string path = Application.StartupPath + @"\Log.txt";
                StreamWriter sWriter = File.CreateText(path);
                sWriter.Write(strLog);
                sWriter.Flush();
                sWriter.Close();
                MessageBox.Show(string.Format("{0}:{1}", FindResource("tipSuccessSave"), path), "tipSaveData");

                lrtxtDataTran.Text = "";
            }
            catch (Exception ex)
            {
                OnLog(tag, ex);
            }
        }

        private void btn_refresh_comports_Click(object sender, EventArgs e)
        {
            RefreshComPorts();
        }

        private uint DelayTime = 0;

        private void btnInventory_Click_1(object sender, EventArgs e)
        {
            try
            {
                if (btnInventory.Text.Equals(FindResource("StartInventory")))
                {
                    if (!FreqRegionFlag)
                    {
                        reader.GetFrequencyRegion();
                        Thread.Sleep(1);
                    }

                    InventoryCfg inventoryCfg = null;
                    List<InventoryAntenna> list = GetAntennaList();
                    if (list.Count == 0)
                    {
                        MessageBox.Show("Please select an antenna！");
                        return;
                    }
                    Session session = GetSession();
                    Target target = GetTarget();

                    if (radio_btn_realtime_inv.Checked == true)
                    {
                        int repeat = Convert.ToInt32(txtRepeat.Text.Trim());
                        if (cb_use_powerSave.Checked == true)
                        {
                            SelectFlag selectFlag = GetSelectFlag();
                            bool readPhase = (cb_use_Phase.Checked == true ? true : false);
                            int powerSave = Convert.ToInt32(txtPowerSave.Text.Trim());
                            inventoryCfg = new CustomizedSessionTargetInventoryCfg(list, session, target, selectFlag, readPhase, powerSave, repeat);

                        }
                        else if (cb_use_Phase.Checked == true)
                        {
                            SelectFlag selectFlag = GetSelectFlag();
                            bool readPhase = (cb_use_Phase.Checked == true ? true : false);
                            inventoryCfg = new CustomizedSessionTargetInventoryCfg(list, session, target, selectFlag, readPhase, repeat);
                        }
                        else if (cb_use_selectFlags_tempPows.Checked == true)
                        {
                            SelectFlag selectFlag = GetSelectFlag();
                            inventoryCfg = new CustomizedSessionTargetInventoryCfg(list, session, target, selectFlag, repeat);
                        }
                        else
                        {
                            inventoryCfg = new CustomizedSessionTargetInventoryCfg(list, session, target, repeat);
                        }

                        RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipCustomizeTargetSessionInventory")));
                    }
                    else if (radio_btn_fast_inv.Checked == true)
                    {
                        int interval = Convert.ToInt32(txtInterval.Text.Trim());
                        int repeat = Convert.ToInt32(txtRepeat.Text.Trim());
                        if (cb_customized_session_target.Checked == true)
                        {

                            bool readPhase = (cb_use_Phase.Checked == true ? true : false);
                            if (cb_use_selectFlags_tempPows.Checked == true)
                            {
                                SelectFlag selectFlag = GetSelectFlag();
                                List<int> tempPowers = GetTemporaryPowerList();
                                inventoryCfg = new FastSwitchAntInventoryCfg(list, interval, selectFlag,
                                    session, target, readPhase, tempPowers, repeat);
                            }
                            else
                            {
                                int times = Convert.ToInt32(txtOptimize.Text.Trim());
                                Optimize optimize = new Optimize(false, times);
                                int ongoing = Convert.ToInt32(txtOngoing.Text.Trim());
                                int targetQuantity = Convert.ToInt32(txtTargetQuantity.Text.Trim());
                                inventoryCfg = new FastSwitchAntInventoryCfg(list, interval, session,
                                    target, optimize, ongoing, targetQuantity, readPhase, repeat);
                            }
                        }
                        else
                        {
                            inventoryCfg = new FastSwitchAntInventoryCfg(list, interval, repeat);
                        }
                        RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipFastInventory")));
                    } else if (rb_fast_inv.Checked == true)
                    {
                        int repeat = Convert.ToInt32(txtRepeat.Text.Trim());
                        inventoryCfg = new RealTimeInventoryCfg(list, repeat, 1);
                    }                    
                    int executeTime = Convert.ToInt32(mInventoryExeCount.Text.Trim());
                    uint cmdInterval = Convert.ToUInt32(mFastIntervalTime.Text.Trim());
                    DelayTime = cmdInterval;
                    if (-1 != executeTime)
                    {
                        inventoryCfg.ExecuteTime = executeTime;
                        TmpExcute = executeTime;
                    }
                    if (0 != cmdInterval)
                    {
                        inventoryCfg.CmdInterval = cmdInterval;
                        if (cb_IceBoxTest.Checked)
                        {

                            if(null != OATime)
                            {
                                OATime = null;
                            }
                            OATime = new System.Timers.Timer();
                            OATime.Interval = cmdInterval / 2;
                            OATime.Elapsed += OATime_Elapsed;
                        }
                    }
                    if (cb_InvTime.Checked)
                    {
                        int invtime = Convert.ToInt32(tb_InvCntTime.Text.Trim());
                        if (invtime <= 0)
                        {
                            MessageBox.Show("Inventory time is too short, please reset");
                            return;
                        }
                        if(null == InvTime)
                        {
                            InvTime = new System.Timers.Timer();
                            InvTime.Interval = invtime * 1000;
                            InvTime.Elapsed += InvTime_Elapsed;
                        }
                    }
                    if (ReverseTarget)
                    {
                        inventoryCfg.RollBack = ReverseTarget;
                        inventoryCfg.RollBackTimes = stayBTimes;
                    }
                    reader.setInventoryCfg(inventoryCfg);
                    if (inventoryCfg == null)
                    {
                        return;
                    }
                    initSaveLog();
                    tagdb.EnableAutomaticTriggers();
                    tagdb.Clear();
                    tagdb.Repaint();
                    led_total_tagreads.Text = "0";
                    txtCmdTagCount.Text = "0";
                    led_cmd_readrate.Text = "0";
                    led_cmd_execute_duration.Text = "0";
                    led_totalread_count.Text = "0";
                    ledFast_total_execute_time.Text = string.Format("{0:d2}:{1:d2}:{2:d2}:{3:d3}", 0, 0, 0, 0);
                    txtFastMinRssi.Text = "0";
                    txtFastMaxRssi.Text = "0";

                    startInventoryTime = DateTime.Now;
                    StartRead(string.Format("{0}[{1} # {2}ms]", inventoryCfg.Cmd,
                        inventoryCfg.ExecuteTime, inventoryCfg.CmdInterval));
                }
                else if (btnInventory.Text.Equals(FindResource("StopInventory")))
                {
                    StopRead();
                    RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("StopInventory")));
                }
            }
            catch (Exception ex)
            {
                lock (tagdb)
                {
                    tagdb.Repaint();
                }
                OnLog(ex);
            }
        }

        private void InvTime_Elapsed(object sender, System.Timers.ElapsedEventArgs e)
        {
            try
            {
                if (InvTime.Enabled)
                {
                    InvTime.Stop();
                    BeginInvoke(new ThreadStart(delegate ()
                    {
                        btnInventory_Click_1(null, null);
                    }));
                    InvTime = null;
                }
            }
            catch(Exception ex)
            {
                throw ex;
            }
        }

        private void OATime_Elapsed(object sender, System.Timers.ElapsedEventArgs e)
        {
            try
            {
                if (OATime.Enabled)
                {
                    OATime.Stop();
                    if (IceTest)
                    {
                        TmpExcute--;
                        BeginInvoke(new ThreadStart(delegate ()
                        {
                            DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, string.Format("TmpExcute = {0}", TmpExcute));
                            if (TmpExcute > 1)
                            {
                                led_total_tagreads.Text = "0";
                                txtCmdTagCount.Text = "0";
                                led_cmd_readrate.Text = "0";
                                led_cmd_execute_duration.Text = "0";
                                led_totalread_count.Text = "0";
                                ledFast_total_execute_time.Text = string.Format("{0:d2}:{1:d2}:{2:d2}:{3:d3}", 0, 0, 0, 0);
                                txtFastMinRssi.Text = "0";
                                txtFastMaxRssi.Text = "0";
                                tagdb.Clear();
                                tagdb.Repaint();
                            }
                        }));
                    }
                }
            }
            catch (Exception ex)
            {
                throw ex;
            }
        }

        private string RevertToTime(long millisecond)//转换为时分秒格式
        {
            long hour = 0;
            long minute = 0;
            long second = 0;
            long ms = 0;
            second = millisecond / 1000;
            ms = millisecond % 1000;
            if (second > 60)
            {
                minute = second / 60;
                second = second % 60;
            }
            if (minute > 60)
            {
                hour = minute / 60;
                minute = minute % 60;
            }
            return string.Format("{0:d2}:{1:d2}:{2:d2} {3:d3}", hour, minute, second, ms);
        }

        private void StartRead(string message)
        {
            try
            {
                if (reader != null && !reader.IsInventorying())
                {
                    btnInventory.Text = FindResource("StopInventory");
                    dispatcherTimer.Start();
                    readratePerSecond.Start();
                    reader.TagRead += Reader_TagRead;
                    reader.ReadTagCountCallback += Reader_ReadTagCountCallback;
                    if(ModelFlag == 2)
                    {
                        if (rb_fast_inv.Checked == true)
                        {
                            int repeat = Convert.ToInt32(txtRepeat.Text.Trim());
                            reader.E710FastInventory(repeat, 0);
                            if (null != InvTime)
                            {
                                InvTime.Start();
                            }
                            return;
                        }
                    }
                    reader.CommandStatistics += Reader_CommandStatistics;
                    if (cb_InvTime.Checked)
                    {
                        if (null != InvTime)
                        {
                            InvTime.Start();
                        }
                    }

                    reader.StartReading();
                    CommunicateFlag = false;
                    if(null == MonitorTime)
                    {
                        MonitorTime = new System.Timers.Timer();
                        MonitorTime.Interval = 100;
                        MonitorTime.Elapsed += MonitorTime_Elapsed;
                        MonitorTime.Start();
                    }
                }
            }
            catch (Exception ex)
            {
                throw ex;
            }
        }

        private void MonitorTime_Elapsed(object sender, System.Timers.ElapsedEventArgs e)
        {
            if (MonitorTime.Enabled)
            {
                if (CommunicateFlag)
                {

                }
                else
                {
                    CommunicateFlag = false;
                }
                MonitorTime.Stop();
                MonitorTime = null;
            }
        }

        private void Reader_ReadTagCountCallback(object sender, ReadTagCountEventArgs e)
        {
            if (IceTest)
            {
                BeginInvoke(new ThreadStart(delegate ()
                {
                    CommunicateFlag = true;
                    //DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, string.Format("e.ReadTagCount = {0}", e.ReadTagCount));
                    if (e.ReadTagCount > 0)
                    {
                        led_total_tagreads.Text = "0";
                        txtCmdTagCount.Text = "0";
                        led_cmd_readrate.Text = "0";
                        led_cmd_execute_duration.Text = "0";
                        led_totalread_count.Text = "0";
                        ledFast_total_execute_time.Text = string.Format("{0:d2}:{1:d2}:{2:d2}:{3:d3}", 0, 0, 0, 0);
                        txtFastMinRssi.Text = "0";
                        txtFastMaxRssi.Text = "0";
                        tagdb.Clear();
                        tagdb.Repaint();
                    }
                }));
            }
        }

        public void StopRead()
        {
            try
            {
                if (CommunicateFlag == true)
                {
                    if (reader.IsInventorying())
                    {
                        dispatcherTimer.Stop();
                        readratePerSecond.Stop();
                        if (ModelFlag == 2)
                        {
                            if (rb_fast_inv.Checked == true)
                            {
                                int repeat = Convert.ToInt32(txtRepeat.Text.Trim());
                                reader.E710FastInventory(repeat, 1);
                                btnInventory.Text = string.Format("{0}", FindResource("StartInventory"));
                                closeLog();
                                reader.TagRead -= Reader_TagRead;
                                reader.ReadTagCountCallback -= Reader_ReadTagCountCallback;
                                return;
                            }
                        }
                        reader.StopReading();
                        CommunicateFlag = false;
                        if (null == MonitorTime)
                        {
                            MonitorTime = new System.Timers.Timer();
                            MonitorTime.Interval = 100;
                            MonitorTime.Elapsed += MonitorTime_Elapsed;
                            MonitorTime.Start();
                        }
                        if (!reader.IsReading())
                        {
                            closeLog();
                            reader.TagRead -= Reader_TagRead;
                            reader.ReadTagCountCallback -= Reader_ReadTagCountCallback;
                            reader.CommandStatistics -= Reader_CommandStatistics;
                            btnInventory.Text = string.Format("{0}", FindResource("StartInventory"));
                        }
                    }
                }
                else
                {
                    reader.StopReading();
                    dispatcherTimer.Stop();
                    readratePerSecond.Stop();
                    closeLog();
                    reader.TagRead -= Reader_TagRead;
                    reader.ReadTagCountCallback -= Reader_ReadTagCountCallback;
                    reader.CommandStatistics -= Reader_CommandStatistics;
                    btnInventory.Text = string.Format("{0}", FindResource("StartInventory"));

                }
                if (cb_InvTime.Checked)
                {
                    if(null != InvTime)
                    {
                        InvTime.Stop();
                        InvTime = null;
                    }
                }
            }
            catch (Exception ex)
            {
                throw ex;
            }
        }

        private void Reader_TagRead(object sender, TagReadDataEventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                CommunicateFlag = true;
                lock (tagdb)
                {
                    tagdb.Add(e.TagData);
                    tagdbTmp.Add(e.TagData);
                    TimeSpan span = DateTime.Now - startInventoryTime;
                    long ts = span.Hours * 60 * 60 * 1000 + span.Minutes * 60 * 1000 + span.Seconds * 1000 + span.Milliseconds;
                    //int executeTime = Convert.ToInt32(mInventoryExeCount.Text.Trim());
                    //if (executeTime != -1)
                    //{
                    //    ledFast_total_execute_time.Text = RevertToTime(ts);
                    //}
                    ledFast_total_execute_time.Text = RevertToTime(ts);
                    led_total_tagreads.Text = string.Format("{0}", tagdb.UniqueTagCounts);
                    led_totalread_count.Text = string.Format("{0}", tagdb.TotalReadCounts);
                    txtFastMinRssi.Text = string.Format("{0}dBm", tagdb.MinRSSI);
                    txtFastMaxRssi.Text = string.Format("{0}dBm", tagdb.MaxRSSI);

                    //DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, "有标签来了");
                }
            }));
        }

        private List<InventoryAntenna> GetAntennaList()
        {
            List<InventoryAntenna> list = new List<InventoryAntenna>();
            try
            {
                //
                if (radio_btn_realtime_inv.Checked || rb_fast_inv.Checked) 
                {
                    fast_inv_ants[combo_realtime_inv_ants.SelectedIndex].Checked = true;
                    list.Add(new InventoryAntenna((Antenna)Enum.ToObject(typeof(Antenna), combo_realtime_inv_ants.SelectedIndex), 0));
                }
                else
                {
                    for (int i = 0; i < (int)channels; i++)
                    {
                        if (fast_inv_ants[i].Checked == true)
                        {
                            list.Add(new InventoryAntenna((Antenna)Enum.ToObject(typeof(Antenna), i), Convert.ToInt32(fast_inv_stays[i].Text.Trim())));
                        }
                    }
                }
            }
            catch (Exception ex)
            {
                throw ex;
            }
            DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, "GetAntennaList {0}", list.Count);
            return list;
        }

        private Target GetTarget()
        {
            if (radio_btn_target_A.Checked == true)
            {
                return Target.A;
            }
            else if (radio_btn_target_B.Checked == true)
            {
                return Target.B;
            }
            else
            {
                throw new Exception("please select a Target parameter");
            }
        }

        private Session GetSession()
        {
            if (radio_btn_S0.Checked == true)
            {
                return Session.S0;
            }
            else if (radio_btn_S1.Checked == true)
            {
                return Session.S1;
            }
            else if (radio_btn_S2.Checked == true)
            {
                return Session.S2;
            }
            else if (radio_btn_S3.Checked == true)
            {
                return Session.S3;
            }
            else
            {
                throw new Exception("please select a Session parameter");
            }
        }

        private List<int> GetTemporaryPowerList()
        {
            List<int> list = new List<int>();
            for (int i = 0; i < 16; i++)
            {
                if (fast_inv_ants[i].Checked == true)
                {
                    list.Add(Convert.ToInt32(fast_inv_temp_pows[i].Text.Trim()));
                }
                else
                {
                    list.Add(20);
                }
            }
            return list;
        }

        private SelectFlag GetSelectFlag()
        {
            if (radio_btn_sl_00.Checked == true)
            {
                return SelectFlag.SL0;
            }
            else if (radio_btn_sl_01.Checked == true)
            {
                return SelectFlag.SL1;
            }
            else if (radio_btn_sl_02.Checked == true)
            {
                return SelectFlag.SL2;
            }
            else if (radio_btn_sl_03.Checked == true)
            {
                return SelectFlag.SL3;
            }
            else
            {
                throw new Exception("please select a SelectFlag parameter");
            }
        }

        private void btnGetTagOpWorkAnt_Click(object sender, EventArgs e)
        {
            try
            {
                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("GetWorkAntenna")));
                reader.GetWorkAntenna();
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnSetTagOpWorkAnt_Click(object sender, EventArgs e)
        {
            try
            {
                if (cmbbxTagOpWorkAnt.SelectedItem == null)
                {
                    MessageBox.Show(string.Format("{0}", FindResource("SelectAntenna")));
                    return;
                }
                Antenna antenna = (Antenna)cmbbxTagOpWorkAnt.SelectedIndex;
                RecordOpHistory(HistoryType.Normal, string.Format("{0} {1}", FindResource("SetWorkAntenna"), antenna));
                reader.SetWorkAntenna(antenna);

                //RecordOpResultsHistory(string.Format("{0} {1}", FindResource("SetWorkAntenna"), antenna), errorCode);
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnGetMonzaStatus_Click(object sender, EventArgs e)
        {
            try
            {
                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipGetMonzaStatus")));
                reader.GetImpinjFastTid();
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnSetMonzaStatus_Click(object sender, EventArgs e)
        {
            try
            {
                bool fastTidEn = false;
                if (rdbMonzaOn.Checked == true)
                {
                    fastTidEn = true;
                }
                else if (rdbMonzaOff.Checked == true)
                {
                    fastTidEn = false;
                }

                RecordOpHistory(HistoryType.Normal, string.Format("{0} {1}", FindResource("tipSetMonzaStatus"), fastTidEn));
                reader.SetAndSaveImpinjFastTid(fastTidEn);
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnGetIdentifier_Click(object sender, EventArgs e)
        {
            try
            {
                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("GetReaderIdentifier")));
                reader.GetReaderIdentifier();
                
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnSetIdentifier_Click(object sender, EventArgs e)
        {
            try
            {
                string identifier = string.Format("{0}", htbSetIdentifier.Text.Trim().Replace(" ", ""));
                if(identifier.Length < 1) 
                {
                    MessageBox.Show(String.Format("{0}", FindResource("tipValueIsNotNull")));
                    return;
                }

                if (!ReaderUtils.CheckIsNByteString(identifier, 2))
                {
                    throw new Exception(string.Format("{0}", FindResource("TipHexStringFotmatError")));
                }
                RecordOpHistory(HistoryType.Normal, string.Format("{0} {1}", FindResource("SetReaderIdentifier"), identifier));
                reader.SetReaderIdentifier(identifier);
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnReaderSetupRefresh_Click(object sender, EventArgs e)
        {
            htxtReadId.Text = "";
            htbGetIdentifier.Text = "";
            htbSetIdentifier.Text = "";
            txtFirmwareVersion.Text = "";
            txtReaderTemperature.Text = "";
            rdbGpio1High.Checked = false;
            rdbGpio1Low.Checked = false;
            rdbGpio2High.Checked = false;
            rdbGpio2Low.Checked = false;
            rdbGpio3High.Checked = false;
            rdbGpio3Low.Checked = false;
            rdbGpio4High.Checked = false;
            rdbGpio4Low.Checked = false;

            cmbSetBaudrate.SelectedIndex = -1;
        }

        private void btnRfSetup_Click(object sender, EventArgs e)
        {
            //txtOutputPower.Text = "";
            tb_outputpower_1.Text = "";
            tb_outputpower_2.Text = "";
            tb_outputpower_3.Text = "";
            tb_outputpower_4.Text = "";
            tb_outputpower_5.Text = "";
            tb_outputpower_6.Text = "";
            tb_outputpower_7.Text = "";
            tb_outputpower_8.Text = "";
            tb_outputpower_9.Text = "";
            tb_outputpower_10.Text = "";
            tb_outputpower_11.Text = "";
            tb_outputpower_12.Text = "";
            tb_outputpower_13.Text = "";
            tb_outputpower_14.Text = "";
            tb_outputpower_15.Text = "";
            tb_outputpower_16.Text = "";

            cmbFrequencyStart.SelectedIndex = -1;
            cmbFrequencyEnd.SelectedIndex = -1;
            tbAntDectector.Text = "";

            //rdbDrmModeOpen.Checked = false;
            //rdbDrmModeClose.Checked = false;

            rdbMonzaOn.Checked = false;
            rdbMonzaOff.Checked = false;
            rdbRegionFcc.Checked = false;
            rdbRegionEtsi.Checked = false;
            rdbRegionChn.Checked = false;

            textReturnLoss.Text = "";
            cmbWorkAnt.SelectedIndex = -1;
            textStartFreq.Text = "";
            TextFreqInterval.Text = "";
            textFreqQuantity.Text = "";
        }
        
        private void btnReturnLoss_Click(object sender, EventArgs e)
        {
            try
            {
                Frequency freq = (Frequency)cmbReturnLossFreq.SelectedIndex;
                RecordOpHistory(HistoryType.Normal, string.Format("{0} @{1}", FindResource("GetRfPortReturnLoss"), freq));
                reader.GetRfPortReturnLoss(freq);
                //RecordOpHistory(HistoryType.Success, string.Format("{0} {1} dB@{2}", FindResource("GetRfPortReturnLoss"), returnLoss, freq));
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnSetProfile_Click(object sender, EventArgs e)
        {

        }

        private void btnGetProfile_Click(object sender, EventArgs e)
        {
            
        }

        private void btnFastRefresh_Click(object sender, EventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                startInventoryTime = DateTime.Now;
                elapsedTime = 0.0;
                lock (tagdb)
                {
                    tagdb.Clear();
                    tagdb.Repaint();

                    led_total_tagreads.Text = tagdb.UniqueTagCounts.ToString();
                    txtCmdTagCount.Text = "0";
                    led_cmd_readrate.Text = "0";
                    led_cmd_execute_duration.Text = "0";
                    led_totalread_count.Text = tagdb.TotalReadCounts.ToString();
                    ledFast_total_execute_time.Text = string.Format("{0:d2}:{1:d2}:{2:d2}:{3:d3}", 0, 0, 0, 0);
                    txtFastMinRssi.Text = tagdb.MinRSSI.ToString();
                    txtFastMaxRssi.Text = tagdb.MaxRSSI.ToString();
                }
            }));
        }

        private void btnSetTagMask_Click(object sender, EventArgs e)
        {
            try
            {
                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipMustBeOptions")));
                SelectFunction function = (SelectFunction)(combo_mast_id.SelectedIndex + 1);
                SessionID target = (SessionID)cmbbxSessionId.SelectedItem;
                SelectAction action = (SelectAction)combo_action.SelectedIndex;
                MemBank bank = (MemBank)combo_menbank.SelectedIndex;
                int startMaskAddr = Convert.ToInt32(startAddr.Text.Trim());
                int maskBitLen = Convert.ToInt32(bitLen.Text.Trim());
                if (startMaskAddr > 255 || maskBitLen > 255)
                {
                    MessageBox.Show(string.Format("{0} startAddr/len [0, 255]", FindResource("TipLengthRange")));
                    return;
                }
                string strMask = hexTextBox_mask.Text.Trim().Replace(" ", "");
                if(maskBitLen > strMask.Length * 4)
                {
                    MessageBox.Show(String.Format("Mask Length({0}) is invaild!The actual len is {1}", (strMask.Length * 4), maskBitLen));
                    return;
                }
                if (!ReaderUtils.CheckIsNByteString(strMask, 1))
                {
                    throw new Exception(string.Format("{0}", FindResource("TipByteStringFotmatError")));
                }

                DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, "strMask={0}", strMask);
                if ((strMask.Length % 2) != 0)
                {
                    strMask = strMask.Insert(strMask.Length - 1, "0");
                    DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, "Insert strMask={0}", strMask);
                }
                byte[] mask = ByteUtils.FromHex(strMask);
                DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, "length={0}", mask.Length);

                int truncate = 0;
                Select select = new Select(function, target, action, bank, startMaskAddr, maskBitLen, mask, truncate);
                reader.Select(select);
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnClearTagMask_Click(object sender, EventArgs e)
        {
            try
            {
                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipClearTagMask")));
                SelectFunction function = (SelectFunction)combo_mast_id_Clear.SelectedIndex;
                reader.ClearSelect(function);
                if (function == SelectFunction.MaskAll)
                {
                    tagMaskDB.Clear();
                }
                else
                {
                    tagMaskDB.Remove(function);
                }
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnGetTagMask_Click(object sender, EventArgs e)
        {
            try
            {
                RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipTagMask")));
                reader.QuerySelect();
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void btnSaveTags_Click(object sender, EventArgs e)
        {
            saveFastData();
        }

#endregion btnXxx

#region CheckedChanged
        private void connectType_CheckedChanged(object sender, EventArgs e)
        {
            if (radio_btn_rs232.Checked)
            {
                grb_rs232.Visible = true;
                grb_tcp.Visible = false;
                btnConnect.Enabled = true;
            }
            else if (radio_btn_tcp.Checked)
            {
                grb_rs232.Visible = false;
                grb_tcp.Visible = true;
                btnConnect.Enabled = true;
            }
        }

        private void rdbRegionFcc_CheckedChanged(object sender, EventArgs e)
        {
            cmbFrequencyStart.SelectedIndex = -1;
            cmbFrequencyEnd.SelectedIndex = -1;
            cmbFrequencyStart.Items.Clear();
            cmbFrequencyEnd.Items.Clear();

            float nStart = 902.00f;
            for (int nloop = 0; nloop < 53; nloop++)
            {
                string strTemp = nStart.ToString("0.00");
                cmbFrequencyStart.Items.Add(strTemp);
                cmbFrequencyEnd.Items.Add(strTemp);

                nStart += 0.5f;
            }
        }

        private void rdbRegionEtsi_CheckedChanged(object sender, EventArgs e)
        {
            cmbFrequencyStart.SelectedIndex = -1;
            cmbFrequencyEnd.SelectedIndex = -1;
            cmbFrequencyStart.Items.Clear();
            cmbFrequencyEnd.Items.Clear();

            float nStart = 865.00f;
            for (int nloop = 0; nloop < 7; nloop++)
            {
                string strTemp = nStart.ToString("0.00");
                cmbFrequencyStart.Items.Add(strTemp);
                cmbFrequencyEnd.Items.Add(strTemp);

                nStart += 0.5f;
            }
        }

        private void rdbRegionChn_CheckedChanged(object sender, EventArgs e)
        {
            cmbFrequencyStart.SelectedIndex = -1;
            cmbFrequencyEnd.SelectedIndex = -1;
            cmbFrequencyStart.Items.Clear();
            cmbFrequencyEnd.Items.Clear();

            float nStart = 920.00f;
            for (int nloop = 0; nloop < 11; nloop++)
            {
                string strTemp = nStart.ToString("0.00");
                cmbFrequencyStart.Items.Add(strTemp);
                cmbFrequencyEnd.Items.Add(strTemp);

                nStart += 0.5f;
            }
        }

        private void chkbxReadSensorTag_CheckedChanged(object sender, EventArgs e)
        {
            if (chkbxReadSensorTag.Checked)
            {
                btnStartReadSensorTag.Enabled = true;
                grbSensorType.Enabled = true;
                if (radio_btn_johar_1.Checked)
                {
                    tagdb.SetSensorTag(TagVendor.JoharTag_1);
                    tagOpDb.SetSensorTag(TagVendor.JoharTag_1);
                }
                else
                {
                    tagdb.SetSensorTag(TagVendor.NormalTag);
                    tagOpDb.SetSensorTag(TagVendor.NormalTag);
                    if (btnStartReadSensorTag.Text.Equals(FindResource("Stop")))
                    {
                        btnStartReadSensorTag_Click(null, null);
                    }
                }
            }
            else
            {
                tagdb.SetSensorTag(TagVendor.NormalTag);
                tagOpDb.SetSensorTag(TagVendor.NormalTag);
                btnStartReadSensorTag.Enabled = false;
                grbSensorType.Enabled = false;
            }
        }

        private void ckDisplayLog_CheckedChanged(object sender, EventArgs e)
        {
            if (ckDisplayLog.Checked)
            {
                m_bDisplayLog = true;
            }
            else
            {
                m_bDisplayLog = false;
            }
        }


        private void cbUserDefineFreq_CheckedChanged(object sender, EventArgs e)
        {
            if (cbUserDefineFreq.Checked == true)
            {
                groupBox21.Enabled = false;
                rdbRegionFcc.Checked = false;
                rdbRegionChn.Checked = false;
                rdbRegionEtsi.Checked = false;
                cmbFrequencyStart.SelectedIndex = -1;
                cmbFrequencyEnd.SelectedIndex = -1;
                groupBox23.Enabled = true;
            }
            else
            {
                groupBox21.Enabled = true;
                groupBox23.Enabled = false;
            }
        }

        private void antType_CheckedChanged(object sender, EventArgs e)
        {
            RadioButton btn = (RadioButton)sender;
            if (!btn.Checked)
                return;
            switch (btn.Name)
            {
                case "antType1":
                    channels = Channels.One;
                    break;
                case "antType4":
                    channels = Channels.Four;
                    break;
                case "antType8":
                    channels = Channels.Eight;
                    break;
                case "antType16":
                    channels = Channels.Sixteen;
                    break;
            }

            antList.Clear();
            antList.Add(Antenna.Ant1);
            if ((int)channels > 1)
            {
                antList.Add(Antenna.Ant2);
                antList.Add(Antenna.Ant3);
                antList.Add(Antenna.Ant4);
            }
            if ((int)channels > 4)
            {
                antList.Add(Antenna.Ant5);
                antList.Add(Antenna.Ant6);
                antList.Add(Antenna.Ant7);
                antList.Add(Antenna.Ant8);
            }
            if ((int)channels > 8)
            {
                antList.Add(Antenna.Ant9);
                antList.Add(Antenna.Ant10);
                antList.Add(Antenna.Ant11);
                antList.Add(Antenna.Ant12);
                antList.Add(Antenna.Ant13);
                antList.Add(Antenna.Ant14);
                antList.Add(Antenna.Ant15);
                antList.Add(Antenna.Ant16);
            }

            //set work ant
            this.cmbWorkAnt.Items.Clear();
            cmbbxTagOpWorkAnt.Items.Clear();
            string antPreFix = FindResource("Antenna");
            for (int i = 1; i <= (int)channels; i++)
            {
                cmbWorkAnt.Items.Add(string.Format("{0}{1}", antPreFix, i));
                cmbbxTagOpWorkAnt.Items.Add(string.Format("{0}{1}", antPreFix, i));
                txtbxOutputPows[i - 1].Enabled = true;
            }
            if (16 > (int)channels)
            {
                for (int i = (int)channels + 1; i <= 16; i++)
                {
                    txtbxOutputPows[i - 1].Enabled = false;
                }
            }

            this.cmbWorkAnt.SelectedIndex = 0;

            InventoryTypeChanged(null, null);

            showSelectedAnt();
        }

        private void cb_customized_session_target_CheckedChanged(object sender, EventArgs e)
        {
            if (cb_customized_session_target.Checked)
            {
                cb_fast_inv_reverse_target.Visible = true;
                tb_fast_inv_staytargetB_times.Visible = true;

                if (radio_btn_fast_inv.Checked)
                {
                    tb_fast_inv_reserved_5.Visible = false;
                    grb_sessions.Visible = true; // Session
                    grb_targets.Visible = true; // Target
                    grb_Reserve.Visible = true;

                    cb_use_Phase.Visible = true;
                    cb_use_selectFlags_tempPows.Visible = true;
                    cb_use_optimize.Visible = true;
                    cb_use_Phase_CheckedChanged(null, null);
                    cb_use_selectFlags_tempPows_CheckedChanged(null, null);
                    cb_use_optimize_CheckedChanged(null, null);
                }
                else
                {
                    grb_sessions.Visible = true;
                    grb_targets.Visible = true;

                    cb_use_Phase.Visible = true; // Phase
                    cb_use_selectFlags_tempPows.Visible = true;
                    cb_use_powerSave.Visible = true;
                }
            }
            else
            {
                // Forbid testing the reverse target AB
                cb_fast_inv_reverse_target.Checked = false;
                cb_fast_inv_reverse_target.Visible = false;
                tb_fast_inv_staytargetB_times.Visible = false;

                if (radio_btn_fast_inv.Checked)
                {
                    cb_use_Phase.Checked = false; // Phase
                    cb_use_Phase.Visible = false;

                    cb_use_selectFlags_tempPows.Checked = false;
                    cb_use_selectFlags_tempPows.Visible = false;
                    tb_fast_inv_reserved_5.Visible = true;
                    grb_sessions.Visible = false;
                    grb_targets.Visible = false;
                    grb_Reserve.Visible = false;

                    cb_use_optimize.Checked = false;
                    cb_use_optimize.Visible = false;
                    grb_Optimize.Visible = false;
                }
                else
                {
                    cb_use_Phase.Checked = false; // Phase
                    cb_use_Phase.Visible = false;

                    cb_use_selectFlags_tempPows.Checked = false;
                    cb_use_selectFlags_tempPows.Visible = false;
                    grb_selectFlags.Visible = false;
                    grb_sessions.Visible = false;
                    grb_targets.Visible = false;

                    cb_use_powerSave.Checked = false;
                    cb_use_powerSave.Visible = false;
                    grb_powerSave.Visible = false;
                }
            }
        }

        private void cb_fast_inv_check_all_ant_CheckedChanged(object sender, EventArgs e)
        {
            bool check = cb_fast_inv_check_all_ant.Checked;
            foreach (CheckBox cb in fast_inv_ants)
            {
                if (cb.Visible)
                    cb.Checked = check;
                else
                    cb.Checked = false;
            }
        }

        private void cb_fast_inv_reverse_target_CheckedChanged(object sender, EventArgs e)
        {
            if (cb_fast_inv_reverse_target.Checked)
            {
                ReverseTarget = true;
                invTargetB = false;
                stayBTimes = Convert.ToInt32(tb_fast_inv_staytargetB_times.Text);
            }
            else
            {
                ReverseTarget = false;
            }
        }

        private void cb_use_selectFlags_tempPows_CheckedChanged(object sender, EventArgs e)
        {
            if (cb_use_selectFlags_tempPows.Checked)
            {
                if (radio_btn_fast_inv.Checked)
                {
                    cb_use_optimize.Checked = false;
                    tb_fast_inv_reserved_5.Visible = false; // reserver 5 disable
                    grb_selectFlags.Visible = true;//SL

                    grb_temp_pow_ants_g1.Visible = true;
                    if ((int)channels > 8)
                        grb_temp_pow_ants_g2.Visible = true;
                }
                else
                {
                    grb_selectFlags.Visible = true;
                }
            }
            else
            {
                if (radio_btn_fast_inv.Checked)
                {
                    tb_fast_inv_reserved_5.Visible = true;
                    grb_selectFlags.Visible = false;//SL

                    grb_temp_pow_ants_g1.Visible = false;
                    grb_temp_pow_ants_g2.Visible = false;
                }
                else
                {
                    cb_use_powerSave.Checked = false;
                    cb_use_Phase.Checked = false;
                    grb_selectFlags.Visible = false;
                }
            }
        }

        private void cb_use_Phase_CheckedChanged(object sender, EventArgs e)
        {
            Phase_fast_inv.Visible = cb_use_Phase.Checked;
            if (radio_btn_realtime_inv.Checked && cb_use_Phase.Checked)
            {
                cb_use_selectFlags_tempPows.Checked = true;
            }
        }

        private void cb_use_powerSave_CheckedChanged(object sender, EventArgs e)
        {
            if (cb_use_powerSave.Checked)
            {
                cb_use_selectFlags_tempPows.Checked = true;
                grb_powerSave.Visible = true;
            }
            else
            {
                grb_powerSave.Visible = false;
            }
        }

        private void cb_use_optimize_CheckedChanged(object sender, EventArgs e)
        {
            if (cb_use_optimize.Checked)
            {
                cb_use_selectFlags_tempPows.Checked = false;
                grb_Optimize.Visible = true;
                grb_Ongoing.Visible = true;
                grb_TargetQuantity.Visible = true;
            }
            else
            {
                grb_Optimize.Visible = false;
                grb_Ongoing.Visible = false;
                grb_TargetQuantity.Visible = false;
            }
        }

        private void cb_tagFocus_CheckedChanged(object sender, EventArgs e)
        {
            try
            {
                bool fastTidEn = false;
                if (cb_tagFocus.Checked == true)
                {
                    fastTidEn = true;
                }
                else if (cb_tagFocus.Checked == false)
                {
                    fastTidEn = false;
                }
                RecordOpHistory(HistoryType.Normal, string.Format("{0} {1}", FindResource("SetAndSaveImpinjFastTid"), fastTidEn));
                reader.SetAndSaveImpinjFastTid(fastTidEn);
                //RecordOpResultsHistory(string.Format("{0} {1}", FindResource("SetAndSaveImpinjFastTid"), fastTidEn), errorCode);
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void chkbxReadTagMultiBankEn_CheckedChanged(object sender, EventArgs e)
        {
            grbReadTagMultiBank.Enabled = chkbxReadTagMultiBankEn.Checked;
        }

        private void chkbxSaveLog_CheckedChanged(object sender, EventArgs e)
        {
            if (chkbxSaveLog.Checked)
            {
                if (!saveLog())
                {
                    chkbxSaveLog.Checked = false;
                    return;
                }
                led_total_tagreads.Text = tagdb.UniqueTagCounts.ToString();
            }
            else
            {
                closeLog();
                led_total_tagreads.Text = tagdb.UniqueTagCounts.ToString();
            }
        }

        private void fastInvAntChecked(object sender, EventArgs e)
        {
            CheckBox cb = (CheckBox)sender;
            int antNo = Convert.ToInt32(cb.Text) - 1;
            if (cb.Checked)
            {
                fast_inv_stays[antNo].Text = "1";
                fast_inv_temp_pows[antNo].Enabled = true;
            }
            else
            {
                fast_inv_stays[antNo].Text = "0";
                fast_inv_temp_pows[antNo].Text = "20";
                fast_inv_temp_pows[antNo].Enabled = false;
            }
        }

        private void MembankCheckChanged(object sender, EventArgs e)
        {
            if (rdbEpc.Checked)
            {
                tb_startWord.Text = "2";
            }
            else
            {
                tb_startWord.Text = "0";
            }
        }
#endregion CheckedChanged

#region TextChanged

        private void textBox1_TextChanged(object sender, EventArgs e)
        {
            if (!CheckPower(tb_outputpower_1.Text))
            {
                tb_outputpower_1.Text = "";
                return;
            }
            int channels = 1;

            if (antType4.Checked)
            {
                channels = 4;
            }

            if (antType8.Checked)
            {
                channels = 8;
            }

            if (antType16.Checked)
            {
                channels = 16;
            }

            if (channels >= 4)
            {
                tb_outputpower_2.Text = tb_outputpower_1.Text;
                tb_outputpower_3.Text = tb_outputpower_1.Text;
                tb_outputpower_4.Text = tb_outputpower_1.Text;

                if (channels >= 8)
                {
                    tb_outputpower_5.Text = tb_outputpower_1.Text;
                    tb_outputpower_6.Text = tb_outputpower_1.Text;
                    tb_outputpower_7.Text = tb_outputpower_1.Text;
                    tb_outputpower_8.Text = tb_outputpower_1.Text;

                    if (channels >= 16)
                    {
                        tb_outputpower_9.Text = tb_outputpower_1.Text;
                        tb_outputpower_10.Text = tb_outputpower_1.Text;
                        tb_outputpower_11.Text = tb_outputpower_1.Text;
                        tb_outputpower_12.Text = tb_outputpower_1.Text;

                        tb_outputpower_13.Text = tb_outputpower_1.Text;
                        tb_outputpower_14.Text = tb_outputpower_1.Text;
                        tb_outputpower_15.Text = tb_outputpower_1.Text;
                        tb_outputpower_16.Text = tb_outputpower_1.Text;
                    }
                }
            }

        }

        private void textBox2_TextChanged(object sender, EventArgs e)
        {
            if (!CheckPower(tb_outputpower_2.Text))
            {
                tb_outputpower_2.Text = "";
                return;
            }
        }

        private void textBox3_TextChanged(object sender, EventArgs e)
        {
            if (!CheckPower(tb_outputpower_3.Text))
            {
                tb_outputpower_3.Text = "";
                return;
            }
        }

        private void textBox4_TextChanged(object sender, EventArgs e)
        {
            if (!CheckPower(tb_outputpower_4.Text))
            {
                tb_outputpower_4.Text = "";
                return;
            }
        }

        private void textBox7_TextChanged(object sender, EventArgs e)
        {
            if (!CheckPower(tb_outputpower_5.Text))
            {
                tb_outputpower_5.Text = "";
                return;
            }
        }

        private void textBox8_TextChanged(object sender, EventArgs e)
        {
            if (!CheckPower(tb_outputpower_6.Text))
            {
                tb_outputpower_6.Text = "";
                return;
            }
        }

        private void textBox9_TextChanged(object sender, EventArgs e)
        {
            if (!CheckPower(tb_outputpower_7.Text))
            {
                tb_outputpower_7.Text = "";
                return;
            }
        }

        private void textBox10_TextChanged(object sender, EventArgs e)
        {
            if (!CheckPower(tb_outputpower_8.Text))
            {
                tb_outputpower_8.Text = "";
                return;
            }
        }


        private void txtInterval_TextChanged(object sender, EventArgs e)
        {

        }

        private void tb_fast_inv_reserved_1_TextChanged(object sender, EventArgs e)
        {

        }

        private void tb_fast_inv_reserved_2_TextChanged(object sender, EventArgs e)
        {

        }

        private void tb_fast_inv_reserved_3_TextChanged(object sender, EventArgs e)
        {

        }

        private void tb_fast_inv_reserved_4_TextChanged(object sender, EventArgs e)
        {

        }

        private void tb_fast_inv_reserved_5_TextChanged(object sender, EventArgs e)
        {

        }

        private void txtOptimize_TextChanged(object sender, EventArgs e)
        {
           
        }

        private void txtOngoing_TextChanged(object sender, EventArgs e)
        {
          
        }

        private void txtTargetQuantity_TextChanged(object sender, EventArgs e)
        {

        }

        private void txtPowerSave_TextChanged(object sender, EventArgs e)
        {

        }

        private void txtRepeat_TextChanged(object sender, EventArgs e)
        {

        }

#endregion TextChanged

#region getParams
        private byte getParamSelectFlag()
        {
            for (int i = 0; i < selectFlagArr.Length; i++)
            {
                if (selectFlagArr[i].Checked)
                    return (byte)i;
            }
            return 0x00;//default SL00
        }

        private byte getParamTarget()
        {
            for (int i = 0; i < targetArr.Length; i++)
            {
                if (targetArr[i].Checked)
                    return (byte)i;
            }
            return 0x00;//default target A
        }

        private byte getParamSession()
        {
            for (int i = 0; i < sessionArr.Length; i++)
            {
                if (sessionArr[i].Checked)
                    return (byte)i;
            }
            return 0x01;//default S1
        }

        private byte getMembank()
        {
            if (rdbReserved.Checked)
            {
                return 0x00;
            }
            else if (rdbEpc.Checked)
            {
                return 0x01;
            }
            else if (rdbTid.Checked)
            {
                return 0x02;
            }
            else if (rdbUser.Checked)
            {
                return 0x03;
            }
            else
            {
                MessageBox.Show(FindResource("tipSelectMemBank"));
                return 0x00;
            }
        }

#endregion getParams

#region Events
        private void htxtSendData_Leave(object sender, EventArgs e)
        {
            string input = htxtSendData.Text.Trim().Replace(" ", "");
            int len = input.Length;
            if (len > 0)
            {
                if (ReaderUtils.CheckIsNByteString(input, 2))
                {
                    byte[] checkData = ByteUtils.FromHex(input);
                    htxtCheckData.Text = string.Format("{0:X2}", ReaderUtils.CheckSum(checkData, 0, checkData.Length));
                }
            }
        }

        private void lrtxtDataTran_DoubleClick(object sender, EventArgs e)
        {
            lrtxtDataTran.Text = "";
        }

        private void lrtxtLog_DoubleClick(object sender, EventArgs e)
        {
            lrtxtLog.Text = "";
        }

        private void cmbSetAccessEpcMatch_DropDown(object sender, EventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate () {
                cmbSetAccessEpcMatch.Items.Clear();

                foreach (TagRecord trd in tagdb.TagList)
                {
                    cmbSetAccessEpcMatch.Items.Add(trd.EPC);
                }

                foreach (TagRecord trd in tagOpDb.TagList)
                {
                    if (!cmbSetAccessEpcMatch.Items.Contains(trd.EPC))
                        cmbSetAccessEpcMatch.Items.Add(trd.EPC);
                }
            }));
        }

        private void InventoryTypeChanged(object sender, EventArgs e)
        {
            if (radio_btn_fast_inv.Checked)
            {
                chkbxReadBuffer.Visible = false;
                grb_multi_ant.Visible = true;
                grb_inventory_cfg.Visible = true;

                cb_use_powerSave.Checked = false;
                cb_use_powerSave.Visible = false;
                grb_real_inv_ants.Visible = false;

                grb_Interval.Visible = true;//Interval
                grb_Reserve.Visible = false;

                cb_customized_session_target.Enabled = true;
                cb_customized_session_target.Checked = false;
                cb_use_selectFlags_tempPows.Checked = false;
                cb_use_selectFlags_tempPows.Text = FindResource("useCmd8A25");
                cb_use_selectFlags_tempPows.Visible = false;
                grb_selectFlags.Visible = false;//SL

                grb_sessions.Visible = false;//Session
                grb_targets.Visible = false;//Target
                grb_temp_pow_ants_g1.Visible = false;//Power
                grb_temp_pow_ants_g2.Visible = false;

                cb_use_powerSave.Checked = false;
                grb_powerSave.Visible = false;

                grb_ants_g1.Visible = true;//Antenna 
                if ((int)channels > 8)
                {
                    grb_ants_g2.Visible = true;
                }
                else
                {
                    grb_ants_g2.Visible = false;
                }
                for (int i = 0; i < 16; i++)
                {
                    if (i < (int)channels)
                    {
                        if (i == 0)
                        {
                            fast_inv_ants[i].Checked = true;
                        }
                        fast_inv_ants[i].Visible = true;
                        fast_inv_stays[i].Visible = true;
                        fast_inv_temp_pows[i].Visible = true;
                    }
                    else
                    {
                        fast_inv_ants[i].Visible = false;
                        fast_inv_stays[i].Visible = false;
                        fast_inv_temp_pows[i].Visible = false;
                    }
                }

                cb_use_optimize.Checked = false;
                cb_use_optimize.Visible = false;
                grb_Optimize.Visible = false;
                grb_Ongoing.Visible = false;
                grb_TargetQuantity.Visible = false;

                cb_use_Phase.Checked = false;
                cb_use_Phase.Visible = false;//Phase
                grb_Repeat.Visible = true;//Repeat
                cb_customized_session_target_CheckedChanged(null, null);
            }
            else if (radio_btn_realtime_inv.Checked)
            {
                chkbxReadBuffer.Visible = false;
                grb_multi_ant.Visible = false;
                grb_inventory_cfg.Visible = true;

                grb_ants_g1.Visible = false;//Antenna
                grb_ants_g2.Visible = false;
                grb_temp_pow_ants_g1.Visible = false;//Power
                grb_temp_pow_ants_g2.Visible = false;

                grb_real_inv_ants.Visible = true;
                antLists.Clear();
                for (int i = 1; i <= (int)channels; i++)
                {
                    antLists.Add(string.Format("{0}{1}", FindResource("Antenna"), i));
                }
                combo_realtime_inv_ants.Items.Clear();
                combo_realtime_inv_ants.Items.AddRange(antLists.ToArray());
                combo_realtime_inv_ants.SelectedIndex = 0;

                grb_Interval.Visible = false;//Interval
                grb_Reserve.Visible = false;

                cb_customized_session_target.Checked = true; // for disable use 89 Cmd
                cb_customized_session_target.Enabled = false;
                cb_use_selectFlags_tempPows.Checked = false;
                cb_use_selectFlags_tempPows.Text = "SL";
                grb_selectFlags.Visible = false;

                grb_sessions.Visible = false;
                grb_targets.Visible = false;

                cb_use_powerSave.Checked = false;
                grb_powerSave.Visible = false;

                cb_use_optimize.Checked = false;
                cb_use_optimize.Visible = false;
                grb_Optimize.Visible = false;
                grb_Ongoing.Visible = false;
                grb_TargetQuantity.Visible = false;

                cb_use_Phase.Checked = false;
                cb_use_Phase.Visible = false;//Phase

                grb_Repeat.Visible = true;//Repeat
                cb_customized_session_target_CheckedChanged(null, null);
            }else if(rb_fast_inv.Checked == true)
            {
                grb_multi_ant.Visible = false;
                grb_inventory_cfg.Visible = false;
                grb_real_inv_ants.Visible = true;

                grb_Interval.Visible = false;//Interval
                grb_Reserve.Visible = false;
                grb_selectFlags.Visible = false;//SL

                grb_sessions.Visible = false;//Session
                grb_targets.Visible = false;//Target
                grb_temp_pow_ants_g1.Visible = false;//Power
                grb_temp_pow_ants_g2.Visible = false;
                grb_powerSave.Visible = false;

                grb_ants_g1.Visible = false;//Antenna 
                grb_Optimize.Visible = false;
                grb_Ongoing.Visible = false;
                grb_TargetQuantity.Visible = false;
                grb_Repeat.Visible = false;//Repeat
            }
        }

        private void dispatcherTimer_Tick(object sender, EventArgs e)
        {
            lock (tagdb)
            {
                tagdb.Repaint();
            }
        }

        private void readRatePerSec_Tick(object sender, EventArgs e)
        {
            if (led_totalread_count.Text.ToString() != "")
            {
                //Divide Total tag count at every 1 sec instant per difference value of
                //current time and start async read time
                CalculateElapsedTime();
            }
        }


#endregion Events

#region Inventory

        /// <summary>
        /// Calculate total elapsed time between present time and start read command
        /// initiated
        /// </summary>
        /// <returns>Returns total time elapsed </returns>
        private double CalculateElapsedTime()
        {

            TimeSpan elapsed = (DateTime.Now - startInventoryTime);
            // elapsed time + previous cached async read time
            double totalseconds = elapsedTime + elapsed.TotalMilliseconds;
            long ts = elapsed.Hours * 60 * 60 * 1000 + elapsed.Minutes * 60 * 1000 + elapsed.Seconds * 1000 + elapsed.Milliseconds;


            //int executeTime = Convert.ToInt32(mInventoryExeCount.Text.Trim());
            //if (executeTime == -1)
            //{
            ledFast_total_execute_time.Text = RevertToTime(ts);
            //    DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, "第{0}执行了", RevertToTime(ts));
            //}



            return totalseconds;
        }

        private double CalculateExecTime()
        {
            return (DateTime.Now - beforeCmdExecTime).TotalMilliseconds;
        }

        /// <summary>
        /// Display read rate per sec
        /// </summary>
        /// <param name="totalElapsedSeconds"> total elapsed time</param>
        private void UpdateReadRate(double totalElapsedSeconds)
        {
    
        }

        private void setInvStoppedStatus()
        {
            dispatcherTimer.Stop();
            readratePerSecond.Stop();
            elapsedTime = CalculateElapsedTime();
            if(OATime != null)
            {
                OATime.Stop();
                OATime = null;
            }
            if(InvTime != null)
            {
                InvTime.Stop();
                InvTime = null;
            }
            if(MonitorTime != null)
            {
                MonitorTime.Stop();
                MonitorTime = null;
            }

            if (reader.IsInventorying())
            {
                reader.StopReading();
            }

            btnInventory.BackColor = Color.WhiteSmoke;
            btnInventory.ForeColor = Color.DarkBlue;
            btnInventory.Text = FindResource("StartInventory");
            // Ensure finally refresh ui
            lock (tagdb)
            {
                tagdb.Repaint();
            }

            ckClearOperationRec.Enabled = true;
        }


        private void saveFastData()
        {
            string strDestinationFile = string.Empty;
            try
            {
                SaveFileDialog saveFileDialog1 = new SaveFileDialog();
                saveFileDialog1.Filter = "CSV Files (*.csv)|*.csv";
                strDestinationFile = "InventoryResult"
                        + DateTime.Now.ToString("yyyy-MM-dd-HH-mm-ss") + @".csv";
                saveFileDialog1.FileName = strDestinationFile;
                if (saveFileDialog1.ShowDialog() == DialogResult.OK)
                {
                    strDestinationFile = saveFileDialog1.FileName;
                    TextWriter tw = new StreamWriter(strDestinationFile, true, Encoding.Default);
                    StringBuilder sb = new StringBuilder();
                    //writing the header
                    int columnCount = dgvInventoryTagResults.Columns.Count;

                    for (int count = 0; count < columnCount; count++)
                    {
                        string colHeader = dgvInventoryTagResults.Columns[count].HeaderText;
                        sb.Append(colHeader + ", ");
                    }
                    tw.WriteLine(sb.ToString());

                    //writing the data
                    TagRecord rda = null;
                    for (int rowCount = 0; rowCount <= tagdb.TagList.Count - 1; rowCount++)
                    {
                        rda = tagdb.TagList[rowCount];
                        textWrite(tw, rda, rowCount + 1);
                    }
                    tw.Close();
                    MessageBox.Show(string.Format("{0}: {1}", FindResource("tipSuccess"), strDestinationFile), FindResource("tipDataExportSuccess"));
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(string.Format("saveFastData {0}", ex.Message));
            }
        }

        /// <summary>
        /// For readability sake in the text file.
        /// </summary>
        /// <param name="tw"></param>
        /// <param name="rda"></param>
        private void textWrite(TextWriter tw, TagRecord rda, int rowNumber)
        {
            StringBuilder sb = new StringBuilder();
            sb.Append(rda.SerialNumber + ", ");

            sb.Append(rda.ReadCount + ", ");

            sb.Append(rda.PC + ", ");

            sb.Append(rda.EPC + ", ");

            sb.Append(rda.Antenna + ", ");

            sb.Append(rda.Rssi + ", ");

            sb.Append(rda.Freq + ", ");

            sb.Append(rda.Phase);

            sb.Append(rda.Data + ", ");

            tw.Write(sb.ToString());
            tw.WriteLine();
        }


        private bool CheckPower(string power)
        {
            if (power.Trim().Length > 0)
            {
                try
                {
                    int tmp = Convert.ToInt16(power.Trim());
                    if (tmp > 33 || tmp < 0)
                    {
                        MessageBox.Show(string.Format("{0},{1}", FindResource("tipInvalidParameter"), FindResource("tipOutPutPowerRange")), "CheckPower");
                        return false;
                    }
                }
                catch (Exception ex)
                {
                    MessageBox.Show(string.Format("CheckPower Error: {0}", ex.Message), "CheckPower");
                    return false;
                }
                return true;
            }
            else
            {
                return false;
            }
        }
#endregion Inventory

        private void RefreshComPorts()
        {
            cmbComPort.Items.Clear();
            string[] portNames = SerialPort.GetPortNames();
            if (portNames != null && portNames.Length > 0)
            {
                cmbComPort.Items.AddRange(portNames);
            }
            cmbComPort.SelectedIndex = cmbComPort.Items.Count - 1;
        }

        public void OnLog(Exception ex)
        {
            BeginInvoke(new ThreadStart(delegate () {
                try
                {
                    if (ex is ReaderCodeException)
                    {
                        ReaderCodeException rex = (ReaderCodeException)ex;
                        if (rex.Code == ErrorCode.NO_TAG_ERROR)
                        {

                        }
                        else if (rex.Code == ErrorCode.PARAMETER_INVALID || rex.Code == ErrorCode.INVENTORY_EXECUTETIME_OVER)
                        {
                            RecordOpHistory(HistoryType.Success, string.Format("{0}: {1} {2}", FindResource("TipSuccess"), rex.Message, ReaderCodeException.faultCodeToMessage(rex.Code)));
                        }
                        else
                        {
                            RecordOpHistory(HistoryType.Failed, string.Format("{0}: {1} {2}", FindResource("TipFailed"), rex.Message, ReaderCodeException.faultCodeToMessage(rex.Code)));
                        }
                    }
                    else if (ex is ReaderCommException || ex is IOException)
                    {
                        RecordOpHistory(HistoryType.Failed, string.Format("{0}: {1}", FindResource("TipFailed"), ex.Message));
                    }
                    else
                    {
                        RecordOpHistory(HistoryType.Failed, string.Format("{0}: {1}", FindResource("TipFailed"), ex.Message));
                        MessageBox.Show(string.Format("Exception: {0}\r\n {1}", ex.Message, ex.StackTrace), string.Format("{0}", FindResource("Error")));
                    }
                }
                catch (Exception ex1)
                {
                    RecordOpHistory(HistoryType.Failed, string.Format("OnLog {0}: {1}", FindResource("TipFailed"), ex.Message));
                    MessageBox.Show(string.Format("OnLog Exception: {0}\r\n {1}", ex1.Message, ex1.StackTrace), string.Format("{0}", FindResource("Error")));
                }
            }));
        }

        private void OnLog(string tag, Exception ex)
        {
            MessageBox.Show(string.Format("{0}:{1}", tag, ex.Message), "Exception");
        }


        public void RecordOpResultsHistory(string record, ErrorCode errorCode)
        {
            if (errorCode == ErrorCode.COMMAND_SUCCESS)
            {
                RecordOpHistory(HistoryType.Success, string.Format("{0}", record));
            }
            else
            {
                RecordOpHistory(HistoryType.Failed, string.Format("{0} {1}, {2}", record, FindResource("TipFailed"), ReaderCodeException.faultCodeToMessage(errorCode)));
            }
        }

        public void RecordOpHistory(HistoryType type, string strLog) 
        {
            WriteLog(lrtxtLog, strLog, type);
        }


        public void WriteLog(LogRichTextBox logRichTxt, string strLog, HistoryType nType)
        {
            logRichTxt.BeginInvoke(new ThreadStart((MethodInvoker)delegate () {
                if (nType == HistoryType.Normal)
                {
                    logRichTxt.AppendTextEx(strLog, Color.Indigo);
                }
                else if (nType == HistoryType.Success)
                {
                    logRichTxt.AppendTextEx(strLog, Color.Blue);
                }
                else if (nType == HistoryType.Failed)
                {
                    logRichTxt.AppendTextEx(strLog, Color.Red);
                }

                if (ckClearOperationRec.Checked)
                {
                    if (logRichTxt.Lines.Length > 50)
                    {
                        logRichTxt.Clear();
                    }
                }
                else
                {
                    if(logRichTxt == lrtxtDataTran)
                    {
                        if (logRichTxt.Lines.Length > 500)
                        {
                            logRichTxt.Clear();
                        }
                    }               
                }

                logRichTxt.Select(logRichTxt.TextLength, 0);
                logRichTxt.ScrollToCaret();
            }));
        }

        private void SetFormEnable(bool bIsEnable)
        {
            gbConnectType.Enabled = (!bIsEnable);
            gbCmdReaderAddress.Enabled = bIsEnable;
            gbCmdVersion.Enabled = bIsEnable;
            gbCmdBaudrate.Enabled = bIsEnable;
            gbCmdTemperature.Enabled = bIsEnable;
            gbCmdOutputPower.Enabled = bIsEnable;
            gbCmdAntenna.Enabled = bIsEnable;
            gbCmdRegion.Enabled = bIsEnable;
            gbCmdBeeper.Enabled = bIsEnable;
            gbCmdReadGpio.Enabled = bIsEnable;
            gbCmdAntDetector.Enabled = bIsEnable;
            gbReturnLoss.Enabled = bIsEnable;
            gbProfile.Enabled = bIsEnable;

            btnResetReader.Enabled = bIsEnable;

            gbCmdOperateTag.Enabled = bIsEnable;

            tab_6c_Tags_Test.Enabled = bIsEnable;

            gbMonza.Enabled = bIsEnable;
            cmbSetBaudrate.Enabled = bIsEnable;
            cmbSetBaudrate.SelectedIndex = -1;
            btnSetUartBaudrate.Enabled = bIsEnable;
            btReaderSetupRefresh.Enabled = bIsEnable;

            btRfSetup.Enabled = bIsEnable;

            gbRfLink.Enabled = bIsEnable;
            grpbQ.Enabled = bIsEnable;

            btE710Refresh.Enabled = bIsEnable;
            gbModel.Enabled = !bIsEnable;

            groupBox24.Enabled = !bIsEnable;

            groupBox32.Enabled = bIsEnable;
            groupBox39.Enabled = bIsEnable;

            btnFactoryReset.Enabled = bIsEnable;
            btn_RefreshSpecial.Enabled = bIsEnable;

        }


        private bool saveLog()
        {
            if (!chkbxSaveLog.Checked || transportLogFile != null)
                return true;
            try
            {
                SaveFileDialog saveFileDialog1 = new SaveFileDialog();
                saveFileDialog1.Filter = "Text Files (.txt)|*.txt";
                saveFileDialog1.Title = FindResource("tipSaveLog");
                string strDestinationFile = "InventoryTesting-log"
                    /*+ DateTime.Now.ToString("yyyy-MM-dd-HH-mm-ss")*/ + @".txt";
                saveFileDialog1.FileName = strDestinationFile;
                saveFileDialog1.InitialDirectory = Application.StartupPath;
                // Show the Dialog.
                // If the user clicked OK in the dialog and
                // a .txt file was selected, open it.
                if (true)//saveFileDialog1.ShowDialog() == DialogResult.OK)
                {
                    StreamWriter writer = new StreamWriter(saveFileDialog1.FileName);
                    writer.AutoFlush = true;
                    transportLogFile = writer;
                    // Todo: add callback
                }

            }
            catch (Exception ex)
            {
                MessageBox.Show(string.Format("cannot saveLog cause {0}", ex.Message), "SaveLog");
                return false;
            }
            return true;
        }

        private void closeLog()
        {
            if (null != transportLogFile)
            {
                transportLogFile.Close();
                transportLogFile = null;

                DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, "closeLog");
            }
        }

#region Johar
        /////
        /// SEN_DATA[23:0] -> EPC 0x06, 0x07
        /// delta1 = User 0x08
        /// Chip version compatible data -> User 0x09
        /// 
        /// 1.Access to raw data
        /// 2.Get SEN_DATA[23:0]
        /// 3.Sensor data verification
        /// 4.Acquisition of calibration parameters user 0x08
        /// 5.Acquisition of temperature data
        /// 
        bool readJoharEn = false;
        bool fastIdEn = false;
        bool joharSelected = false;
        bool readingJohar = false;
        bool readingMultiBank = false;

        private void btnStartReadSensorTag_Click(object sender, EventArgs e)
        {
            if (btnStartReadSensorTag.Text.Equals(FindResource("Start")))
            {
                RefreshTagResult = 0;
                tagOpDb.Clear();
                btnStartReadSensorTag.Text = FindResource("Stop");
                readJoharEn = true;
                chkbxReadSensorTag.Checked = true;
                readingJohar = true;
                reader.SetImpinjFastTidForJohar(true);
            }
            else if (btnStartReadSensorTag.Text.Equals(FindResource("Stop")))
            {
                if (readJoharEn)
                {
                    readingJohar = false;
                    readJoharEn = false;
                    reader.SetImpinjFastTidForJohar(false);
                    if(StartCmdTime == null)
                    {
                        StartCmdTime = new System.Timers.Timer();
                        StartCmdTime.Interval = 100;
                        StartCmdTime.Elapsed += StartCmdTime_Elapsed;
                        StartCmdTime.Start();
                    }

                    btnStartReadSensorTag.Text = FindResource("Start");
                }
            }
        }

        private void StartCmdTime_Elapsed(object sender, System.Timers.ElapsedEventArgs e)
        {
            if (StartCmdTime.Enabled)
            {
                if (fastIdEn)
                {
                    reader.SetImpinjFastTidForJohar(false);
                }
                else
                {
                    StartCmdTime.Stop();
                    StartCmdTime = null;
                }
            }
        }

#endregion Johar

#region NetPort
        UDPThread tUdp = null;

        //NetCard DB
        NetCardDB ncdb = null;
        //NetPort device DB
        NetPortDB netPortDB = null;


        //Initializes the WCH CH9121 device list
        private void initDgvNetPort()
        {
            dgvNetPort.AutoGenerateColumns = false;
            npSerialNumberColumn.DataPropertyName = "SerialNumber";
            npSerialNumberColumn.HeaderText = "#";
            npSerialNumberColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.AllCells;

            npDeviceNameColumn.DataPropertyName = "DeviceName";
            npDeviceNameColumn.HeaderText = FindResource("npDeviceName");
            npDeviceNameColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.AllCells;

            npDeviceIpColumn.DataPropertyName = "DeviceIp";
            npDeviceIpColumn.HeaderText = FindResource("npDeviceIp");
            npDeviceIpColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.AllCells;

            npDeviceMacColumn.DataPropertyName = "DeviceMac";
            npDeviceMacColumn.HeaderText = FindResource("npDeviceMac");
            npDeviceMacColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.AllCells;

            npChipVerColumn.DataPropertyName = "ChipVer";
            npChipVerColumn.HeaderText = FindResource("npChipVer");
            npChipVerColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.AllCells;

            npPcMacColumn.DataPropertyName = "PcMac";
            npPcMacColumn.HeaderText = FindResource("npPcMac");
            npPcMacColumn.AutoSizeMode = DataGridViewAutoSizeColumnMode.AllCells;

            if (netPortDB == null)
                netPortDB = new NetPortDB();
            dgvNetPort.DataSource = null;
            dgvNetPort.DataSource = netPortDB.NetPortList;

        }
#endregion
        //Initializes NetPort UI
        private void initDgvNetPortUI()
        {
            cmbbxPort1_NetMode.DataSource = Enum.GetValues(typeof(NETPORT_TYPE));
            cmbbxPort1_BaudRate.DataSource = Enum.GetValues(typeof(NETPORT_Baudrate));
            cmbbxPort1_DataSize.DataSource = Enum.GetValues(typeof(NETPORT_DataSize));
            cmbbxPort1_StopBits.DataSource = Enum.GetValues(typeof(NETPORT_StopBits));
            cmbbxPort1_Parity.DataSource = Enum.GetValues(typeof(NETPORT_Parity));

            chkbxPort0PortEn_CheckedChanged(null, null);
        }

        private bool CheckUDP()
        {
            if (tUdp == null)
            {
                MessageBox.Show("tUdp is null", "CheckUDP");
                return false;
            }
            return true;
        }

        private void TUdp_NetCommRead(object sender, NetCommEventArgs e)
        {
            if (!CheckUDP())
                return;
            BeginInvoke(new ThreadStart(delegate () {
                tUdp.StopSearchNetPort();
            }));

            NET_COMM comm = e.NetComm;
            if (comm.Cmd == NET_CMD.NET_MODULE_ACK_SEARCH)
            {
                BeginInvoke(new ThreadStart(delegate () {
                    netPortDB.Add(comm);
                    //WriteLog(lrtxtLog, string.Format("Recv: {0}", comm.FoundDev.ToString()), 1);
                }));

                BeginInvoke(new ThreadStart(delegate () {
                    lblNetPortCount.Text = string.Format("{0}: {1}", FindResource("tipNetPortDeviceCount"), netPortDB.GetCount());
                }));
            }
            if (comm.Cmd == NET_CMD.NET_MODULE_ACK_RESEST)
            {
                BeginInvoke(new ThreadStart(delegate () {
                    btnResetNetport.Text = FindResource("npReset");
                    MessageBox.Show(string.Format(FindResource("tipResetNetPortSucess")), "Reset Sucessful");
                }));
                netStartReset = false;
            }
            if (comm.Cmd == NET_CMD.NET_MODULE_ACK_GET
                | comm.Cmd == NET_CMD.NET_MODULE_ACK_SET)
            {
                BeginInvoke(new ThreadStart(delegate ()
                {

                    if (comm.Cmd == NET_CMD.NET_MODULE_ACK_GET)
                    {
                        btnGetNetport.Text = FindResource("npGet");
                        netStartGet = false;
                        MessageBox.Show(string.Format("{0}", FindResource("tipGetNetPortSucess")), "GetCfg Sucessful");
                    }
                    if (comm.Cmd == NET_CMD.NET_MODULE_ACK_SET)
                    {
                        btnSetNetport.Text = FindResource("npSave");
                        netStartSave = false;

                        btnDefaultNetPort.Text = FindResource("npDefault");
                        netStartDefault = false;

                        MessageBox.Show(string.Format("{0}", FindResource("tipSaveOrDefaultNetPortSucess")), "Save/Default Sucessful");
                    }

#region //NET_COMM
                    txtbxHwCfgDeviceName.Text = string.Format("{0}", comm.HWConfig.Modulename);
                    txtbxHwCfgMac.Text = string.Format("{0}", comm.HWConfig.DevMAC);
                    txtbxHwCfgIp.Text = string.Format("{0}", comm.HWConfig.DevIP);
                    txtbxHwCfgMask.Text = string.Format("{0}", comm.HWConfig.DevIPMask);
                    txtbxHwCfgGateway.Text = string.Format("{0}", comm.HWConfig.DevGWIP);
                    chkbxHwCfgDhcpEn.Checked = comm.HWConfig.DhcpEnable;
                    chkbxHwCfgComCfgEn.Checked = comm.HWConfig.ComcfgEn;
                    chkbxPort0PortEn.Checked = comm.PortCfg_0.PortEn;
                    txtbxHeartbeatInterval.Text = string.Format("{0}", comm.PortCfg_0.RxPktTimeout);
                    txtbxHeartbeatContent.Text = string.Format("{0}", comm.PortCfg_0.Domainname);
                    chkbxPort1_PortEn.Checked = comm.PortCfg_1.PortEn;
                    if (cmbbxPort1_NetMode.Items.Contains((NETPORT_TYPE)comm.PortCfg_1.NetMode))
                    {
                        cmbbxPort1_NetMode.SelectedItem = (NETPORT_TYPE)comm.PortCfg_1.NetMode;
                    }
                    else
                    {
                        MessageBox.Show(string.Format("{0}: {1}", FindResource("tipNotSupport"), cmbbxPort1_NetMode.SelectedItem));
                    }
                    chkbxPort1_RandEn.Checked = comm.PortCfg_1.RandSportFlag;
                    txtbxPort1_NetPort.Text = string.Format("{0}", comm.PortCfg_1.NetPort);
                    txtbxPort1_DesIp.Text = string.Format("{0}", comm.PortCfg_1.DesIP);
                    txtbxPort1_DesPort.Text = string.Format("{0}", comm.PortCfg_1.DesPort);

                    if (cmbbxPort1_BaudRate.Items.Contains((NETPORT_Baudrate)comm.PortCfg_1.BaudRate))
                    {
                        cmbbxPort1_BaudRate.SelectedItem = comm.PortCfg_1.BaudRate;
                    }
                    else
                    {
                        MessageBox.Show(string.Format("{0} BaudRate ", FindResource("tipNotSupport"), comm.PortCfg_1.BaudRate));
                        return;
                    }

                    if (cmbbxPort1_DataSize.Items.Contains((NETPORT_DataSize)comm.PortCfg_1.DataSize))
                    {
                        cmbbxPort1_DataSize.SelectedItem = (NETPORT_DataSize)comm.PortCfg_1.DataSize;
                    }
                    else
                    {
                        MessageBox.Show(string.Format("{0} DataSize ", FindResource("tipNotSupport"), comm.PortCfg_1.DataSize));
                        return;
                    }

                    if (cmbbxPort1_StopBits.Items.Contains((NETPORT_StopBits)comm.PortCfg_1.StopBits))
                    {
                        cmbbxPort1_StopBits.SelectedItem = (NETPORT_StopBits)comm.PortCfg_1.StopBits;
                    }
                    else
                    {
                        MessageBox.Show(string.Format("{0} StopBits ", FindResource("tipNotSupport"), comm.PortCfg_1.StopBits));
                        return;
                    }

                    if (cmbbxPort1_Parity.Items.Contains((NETPORT_Parity)comm.PortCfg_1.Parity))
                    {
                        cmbbxPort1_Parity.SelectedItem = (NETPORT_Parity)comm.PortCfg_1.Parity;
                    }
                    else
                    {
                        MessageBox.Show(string.Format("{0} Parity ", FindResource("tipNotSupport"), comm.PortCfg_1.Parity));
                        return;
                    }
                    chkbxPort1_PhyDisconnect.Checked = comm.PortCfg_1.PHYChangeHandle;
                    txtbxPort1_RxPkgLen.Text = string.Format("{0}", comm.PortCfg_1.RxPktlength);
                    txtbxPort1_RxTimeout.Text = string.Format("{0}", comm.PortCfg_1.RxPktTimeout);
                    txtbxPort1_ReConnectCnt.Text = string.Format("{0}", comm.PortCfg_1.ReConnectCnt);
                    chkbxPort1_ResetCtrl.Checked = comm.PortCfg_1.ResetCtrl;
                    txtbxPort1_DnsDomain.Text = string.Format("{0}", comm.PortCfg_1.Domainname);
                    txtbxPort1_DnsIp.Text = string.Format("{0}", comm.PortCfg_1.DNSHostIP);
                    txtbxPort1_Dnsport.Text = string.Format("{0}", comm.PortCfg_1.DNSHostPort);
#endregion //NET_COMM
                }));
            }
        }
        //Search for the network card
        private void btnSearchNetCard_Click(object sender, EventArgs e)
        {
            try
            {
                ManagementObjectSearcher mObjs = new ManagementObjectSearcher("SELECT * FROM Win32_NetworkAdapterConfiguration where IPenabled=true");
                if (mObjs.Get().Count == 0)
                {
                    MessageBox.Show(string.Format("{0}", FindResource("TipNoNetCardFound")));
                    return;
                }
                foreach (ManagementObject mObj in mObjs.Get())
                {
                    string desc = mObj.GetPropertyValue("Description").ToString();
                    string[] ipAddr = (String[])mObj.GetPropertyValue("IPAddress");
                    string pcIpaddr = String.Join(", ", ipAddr, 0, (ipAddr.Length > 1 ? 1 : 0));

                    string[] subNet = (String[])mObj.GetPropertyValue("IPSubnet");
                    string pcMask = String.Join("", subNet, 0, (subNet.Length > 1 ? 1 : 0));

                    string pcMac = mObj.GetPropertyValue("MACAddress").ToString();

                    NetCard nc = new NetCard(desc, pcIpaddr, pcMask, pcMac);
                    ncdb.Add(nc);
                }
                if (cmbbxNetCard.Items.Count > 0)
                {
                    cmbbxNetCard.SelectedIndex = 0;
                    cmbbxNetCard_SelectedIndexChanged(null, null);
                }
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }
        //Switch NetCard
        private void cmbbxNetCard_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (tUdp == null)
            {
                tUdp = new UDPThread();
                tUdp.NetCommRead += TUdp_NetCommRead;
            }

            if (cmbbxNetCard.Items.Count > 0)
            {
                tUdp.CurNetCard = (NetCard)cmbbxNetCard.SelectedItem;
                lblCurNetcard.Text = string.Format("ip:{0}, mask: {1}, mac: ", tUdp.CurNetCard.Ip, tUdp.CurNetCard.Mask);
                lblCurPcMac.Text = string.Format("{0}", tUdp.CurNetCard.Mac);
            }
        }

        private void ClearCfgUI()
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                lblNetPortCount.Text = "";
#region //NET_COMM
                txtbxHwCfgDeviceName.Text = "";
                txtbxHwCfgMac.Text = "";
                txtbxHwCfgIp.Text = "";
                txtbxHwCfgMask.Text = "";
                txtbxHwCfgGateway.Text = "";
                chkbxHwCfgDhcpEn.Checked = false;
                chkbxHwCfgComCfgEn.Checked = false;
                chkbxPort0PortEn.Checked = false;
                txtbxHeartbeatInterval.Text = "";
                txtbxHeartbeatContent.Text = "";
                chkbxPort1_PortEn.Checked = false;
                cmbbxPort1_NetMode.SelectedIndex = -1;
                chkbxPort1_RandEn.Checked = false;
                txtbxPort1_NetPort.Text = "";
                txtbxPort1_DesIp.Text = "";
                txtbxPort1_DesPort.Text = "";
                cmbbxPort1_BaudRate.SelectedIndex = -1;
                cmbbxPort1_DataSize.SelectedIndex = -1;
                cmbbxPort1_StopBits.SelectedIndex = -1;
                cmbbxPort1_Parity.SelectedIndex = -1;
                chkbxPort1_PhyDisconnect.Checked = false;
                txtbxPort1_RxPkgLen.Text = "";
                txtbxPort1_RxTimeout.Text = "";
                txtbxPort1_ReConnectCnt.Text = "";
                chkbxPort1_ResetCtrl.Checked = false;
                txtbxPort1_DnsDomain.Text = "";
                txtbxPort1_DnsIp.Text = "";
                txtbxPort1_Dnsport.Text = "";
#endregion //NET_COMM
            }));
        }
        //Clear the NetPort device list and the NetPort database
        private void btnClearNetPort_Click(object sender, EventArgs e)
        {
            try
            {
                netPortDB.Clear();
                ClearCfgUI();
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void linklblOldNetPortCfgTool_LinkClicked(object sender, EventArgs e)
        {
            string url = "https://drive.263.net/link/41OTclS6USY4fTc/";
            Process.Start(url);
        }

        private void linklblNetPortCfgTool_LinkClicked(object sender, LinkLabelLinkClickedEventArgs e)
        {
            string url = "https://drive.263.net/link/cq8UK5i03uk1huN/";
            Process.Start(url);
        }

        //Search the NetPort device
        bool netStartSearch = false;
        private void btnSearchNetport_Click(object sender, EventArgs e)
        {
            try
            {
                if (!CheckUDP())
                    return;

                if (cmbbxNetCard.SelectedItem == null)
                {
                    MessageBox.Show(string.Format("{0}", FindResource("TipNoDeviceSelect")), "SearchNetport");
                    return;
                }
                if (btnSearchNetport.Text.Equals(FindResource("npSearchNetPort")))
                {
                    BeginInvoke(new ThreadStart(delegate () {
                        Thread t = new Thread(new ThreadStart(delegate ()
                        {
                            netStartSearch = true;
                            while (netStartSearch)
                            {
                                tUdp.StartSearchNetPort();
                                Thread.Sleep(1000);
                            }
                        }));
                        t.Start();
                        btnSearchNetport.Text = FindResource("npSearchingNetPort");
                    }));
                }
                else if (btnSearchNetport.Text.Equals(FindResource("npSearchingNetPort")))
                {
                    netStartSearch = false;
                    btnSearchNetport.Text = FindResource("npSearchNetPort");
                }
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        // Gets NetPort device information
        private void dgvNetPort_DoubleClick(object sender, EventArgs e)
        {
            netStartSearch = false;
            btnGetNetport_Click(null, null);
        }

        bool netStartGet = false;
        private void btnGetNetport_Click(object sender, EventArgs e)
        {
            try
            {
                if (!CheckUDP())
                    return;

                if (btnSearchNetport.Text.Equals(FindResource("SearchingNetPort")))
                {
                    btnSearchNetport_Click(null, null);
                }

                if (netPortDB.GetCount() > 0 && cmbbxNetCard.SelectedIndex != -1)
                {
                    NetPortDevice npd = netPortDB.GetNetPortDeviceByMac((string)dgvNetPort.CurrentRow.Cells[3].Value);

                    if (npd == null)
                    {
                        return;
                    }
                    btnGetNetport.Text = string.Format("{0}", FindResource("Retry"));
                    Thread t = new Thread(new ThreadStart(delegate ()
                    {
                        netStartGet = true;
                        while (netStartGet)
                        {
                            tUdp.GetNetPort(npd);
                            Thread.Sleep(1000);
                        }
                    }));
                    t.Start();
                }
                else
                {
                    MessageBox.Show(string.Format("{0}", FindResource("TipNoDeviceSelect")));
                }
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        // Set NetPort device information
        bool netStartSave = false;
        private void btnSetNetport_Click(object sender, EventArgs e)
        {
            try
            {
                if (!CheckUDP())
                    return;

                if (btnSearchNetport.Text.Equals(FindResource("SearchingNetPort")))
                {
                    btnSearchNetport_Click(null, null);
                }

                if (dgvNetPort.RowCount > 0 && cmbbxNetCard.SelectedIndex != -1)
                {
                    NetPortDevice npd = netPortDB.GetNetPortDeviceByMac((string)dgvNetPort.CurrentRow.Cells[3].Value);
                    BeginInvoke(new ThreadStart(delegate ()
                    {
                        try
                        {
#region HWCfg
                            DeviceHWConfig hwCfg = new DeviceHWConfig();
                            hwCfg.DevType = 0x21;
                            hwCfg.AuxDevType = 0x21;
                            hwCfg.Index = 0x01;
                            hwCfg.DevHardwareVer = 0x02;
                            hwCfg.DevSoftwareVer = 0x06;
                            hwCfg.Modulename = string.Format("{0}", txtbxHwCfgDeviceName.Text.Trim());
                            hwCfg.DevMAC = npd.DeviceMac;
                            hwCfg.DevIP = txtbxHwCfgIp.Text.Trim();
                            hwCfg.DevGWIP = txtbxHwCfgGateway.Text.Trim();
                            hwCfg.DevIPMask = txtbxHwCfgMask.Text.Trim();
                            hwCfg.DhcpEnable = (chkbxHwCfgDhcpEn.Checked == true ? true : false);
                            hwCfg.WebPort = 80;
                            hwCfg.Username = "admin";
                            hwCfg.PassWordEn = false;
                            hwCfg.PassWord = "";
                            hwCfg.UpdateFlag = false;
                            hwCfg.ComcfgEn = (chkbxHwCfgComCfgEn.Checked == true ? true : false);
                            hwCfg.Reserved = "";
#endregion HWCfg

                            DevicePortConfig[] portCfg = new DevicePortConfig[2];
#region Port_0
                            portCfg[0] = new DevicePortConfig();
                            portCfg[0].Index = 0;
                            portCfg[0].PortEn = (chkbxPort0PortEn.Checked == true ? true : false);
                            portCfg[0].NetMode = NETPORT_TYPE.UDP_SERVER;
                            portCfg[0].RandSportFlag = true;
                            portCfg[0].NetPort = 3000;
                            portCfg[0].DesIP = "192.168.1.100";
                            portCfg[0].DesPort = 2000;
                            portCfg[0].BaudRate = NETPORT_Baudrate.B9600;
                            portCfg[0].DataSize = NETPORT_DataSize.Bits8;
                            portCfg[0].StopBits = NETPORT_StopBits.One;
                            portCfg[0].Parity = NETPORT_Parity.None;
                            portCfg[0].PHYChangeHandle = true;
                            portCfg[0].RxPktlength = 1024;
                            portCfg[0].RxPktTimeout = (chkbxPort0PortEn.Checked == true ? Convert.ToInt32(txtbxHeartbeatInterval.Text) : 0);
                            portCfg[0].ReConnectCnt = 0;
                            portCfg[0].ResetCtrl = false;
                            portCfg[0].DNSFlag = false;
                            portCfg[0].Domainname = (chkbxPort0PortEn.Checked == true ? string.Format("{0}", txtbxHeartbeatContent.Text.Trim()) : "");
                            portCfg[0].DNSHostIP = "0.0.0.0";
                            portCfg[0].DNSHostPort = 0;
                            portCfg[0].Reserved = "";
#endregion Port_0

#region Port_1
                            portCfg[1] = new DevicePortConfig();
                            portCfg[1].Index = 1;
                            portCfg[1].PortEn = (chkbxPort1_PortEn.Checked == true ? true : false);
                            portCfg[1].NetMode = (NETPORT_TYPE)cmbbxPort1_NetMode.SelectedItem;
                            portCfg[1].RandSportFlag = (chkbxPort1_RandEn.Checked == true ? true : false); ;
                            portCfg[1].NetPort = Convert.ToInt32(txtbxPort1_NetPort.Text.Trim());
                            portCfg[1].DesIP = txtbxPort1_DesIp.Text.Trim();
                            portCfg[1].DesPort = Convert.ToInt32(txtbxPort1_DesPort.Text.Trim());
                            portCfg[1].BaudRate = (NETPORT_Baudrate)cmbbxPort1_BaudRate.SelectedItem;
                            portCfg[1].DataSize = (NETPORT_DataSize)cmbbxPort1_DataSize.SelectedItem;
                            portCfg[1].StopBits = (NETPORT_StopBits)cmbbxPort1_StopBits.SelectedItem;
                            portCfg[1].Parity = (NETPORT_Parity)cmbbxPort1_Parity.SelectedItem;
                            portCfg[1].PHYChangeHandle = (chkbxPort1_PhyDisconnect.Checked == true ? true : false); ;
                            portCfg[1].RxPktlength = Convert.ToInt32(txtbxPort1_RxPkgLen.Text.Trim());
                            portCfg[1].RxPktTimeout = Convert.ToInt32(txtbxPort1_RxTimeout.Text.Trim());
                            portCfg[1].ReConnectCnt = Convert.ToInt32(txtbxPort1_ReConnectCnt.Text.Trim());
                            portCfg[1].ResetCtrl = (chkbxPort1_ResetCtrl.Checked == true ? true : false); ;
                            portCfg[1].DNSFlag = false;
                            portCfg[1].Domainname = string.Format("{0}", txtbxPort1_DnsDomain.Text.Trim());
                            portCfg[1].DNSHostIP = txtbxPort1_DnsIp.Text.Trim();
                            portCfg[1].DNSHostPort = Convert.ToInt32(txtbxPort1_Dnsport.Text.Trim());
                            portCfg[1].Reserved = "";
#endregion Port_1

                            string pc_mac = lblCurPcMac.Text.ToString();
                            btnSetNetport.Text = string.Format("{0}", FindResource("Retry"));
                            Thread t = new Thread(new ThreadStart(delegate ()
                            {
                                netStartSave = true;
                                while (netStartSave)
                                {
                                    tUdp.SetNetPort(npd, pc_mac, hwCfg, portCfg);
                                    Thread.Sleep(1000);
                                }
                            }));
                            t.Start();
                        }
                        catch (Exception ex)
                        {
                            OnLog(ex);
                        }
                    }));
                }
                else
                {
                    MessageBox.Show(string.Format("{0}", FindResource("TipNoDeviceSelect")));
                }
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        //Reset NetPort device information
        bool netStartReset = false;
        private void btnResetNetport_Click(object sender, EventArgs e)
        {
            try
            {
                if (!CheckUDP())
                    return;
                if (btnSearchNetport.Text.Equals(FindResource("SearchingNetPort")))
                {
                    btnSearchNetport_Click(null, null);
                }
                if (dgvNetPort.RowCount > 0 && cmbbxNetCard.SelectedIndex != -1)
                {
                    NetPortDevice npd = netPortDB.GetNetPortDeviceByMac((string)dgvNetPort.CurrentRow.Cells[3].Value);     
                    if (npd == null)
                    {
                        return;
                    }
                    btnResetNetport.Text = string.Format("{0}", FindResource("Retry"));
                    Thread t = new Thread(new ThreadStart(delegate ()
                    {
                        netStartReset = true;
                        while (netStartReset)
                        {
                            tUdp.ResetNetPort(npd);
                            Thread.Sleep(3000);
                        }
                    }));
                    t.Start();
                }
                else
                {
                    MessageBox.Show(string.Format("{0}", FindResource("TipNoDeviceSelect")));
                }
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        //Set NetPort as the default
        bool netStartDefault = false;

        private void btnDefaultNetPort_Click(object sender, EventArgs e)
        {
            try
            {
                if (!CheckUDP())
                    return;
                if (btnSearchNetport.Text.Equals(FindResource("SearchingNetPort")))
                {
                    btnSearchNetport_Click(null, null);
                }

                if (dgvNetPort.RowCount > 0 && cmbbxNetCard.SelectedIndex != -1)
                {
                    NetPortDevice npd = netPortDB.GetNetPortDeviceByMac((string)dgvNetPort.CurrentRow.Cells[3].Value);
                    if (npd == null)
                    {
                        return;
                    }
                    btnDefaultNetPort.Text = string.Format("{0}", FindResource("Retry"));
                    string pcMac = string.Format("{0}", lblCurPcMac.Text);
                    Thread t = new Thread(new ThreadStart(delegate ()
                    {
                        netStartDefault = true;
                        while (netStartDefault)
                        {
                            tUdp.DefaultNetPort(npd, pcMac);
                            Thread.Sleep(1000);
                        }
                    }));
                    t.Start();
                }
                else
                {
                    MessageBox.Show(string.Format("{0}", FindResource("TipNoDeviceSelect")));
                }
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private void chkbxPort0PortEn_CheckedChanged(object sender, EventArgs e)
        {
            grbHeartbeat.Enabled = chkbxPort0PortEn.Checked;
            if (!chkbxPort0PortEn.Checked)
            {
                txtbxHeartbeatContent.Text = "";
                txtbxHeartbeatInterval.Text = "0";
            }
        }

        private void cmbbxPort1_NetMode_SelectedIndexChanged(object sender, EventArgs e)
        {
            if (cmbbxPort1_NetMode.SelectedIndex == cmbbxPort1_NetMode.Items.IndexOf(NETPORT_TYPE.TCP_SERVER))
            {
                EnableTcpServerUI(false);
            }
            else
            {
                EnableTcpServerUI(true);
            }
        }

        private void EnableTcpServerUI(bool flag)
        {
            chkbxPort1_RandEn.Enabled = flag;
            grbDesIpPort.Enabled = flag;
            grbDnsDomain.Enabled = flag;
        }

        private void chkbxPort1_DomainEn_CheckedChanged(object sender, EventArgs e)
        {
            if (chkbxPort1_DomainEn.Checked)
            {
                grbDnsDomain.Enabled = true;
                grbDesIpPort.Enabled = false;
            }
            else
            {
                grbDnsDomain.Enabled = false;
                grbDesIpPort.Enabled = true;
            }
        }

        private void chkbxPort1_RandEn_CheckedChanged(object sender, EventArgs e)
        {
            if (chkbxPort1_RandEn.Checked)
            {
                txtbxPort1_NetPort.Enabled = false;
            }
            else
            {
                txtbxPort1_NetPort.Enabled = true;
            }
        }

        private byte[] LoadCfg()
        {
            try
            {
                System.Windows.Forms.OpenFileDialog openLoadSaveConfigFileDialog = new System.Windows.Forms.OpenFileDialog();
                openLoadSaveConfigFileDialog.Filter = "NetPortConfigure (.cfg)|*.cfg";
                openLoadSaveConfigFileDialog.Title = string.Format("{0}", FindResource("TipSelectNetPortCfgFile"));
                openLoadSaveConfigFileDialog.InitialDirectory = Directory.GetParent(System.Reflection.Assembly.GetExecutingAssembly().Location).ToString();
                openLoadSaveConfigFileDialog.RestoreDirectory = true;
                if (System.Windows.Forms.DialogResult.OK == openLoadSaveConfigFileDialog.ShowDialog())
                {
                    FileStream fs = new FileStream(openLoadSaveConfigFileDialog.FileName, FileMode.Open, FileAccess.Read, FileShare.ReadWrite);
                    StreamReader sr = new StreamReader(fs);   //选择编码方式
                    StringBuilder cfgStr = new StringBuilder();
                    while (sr.EndOfStream != true)
                    {
                        cfgStr.Append(sr.ReadLine());
                    }
                    //DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG,"cfgStr={0}", cfgStr.Replace(" ", ""));
                    MessageBox.Show(string.Format("{0}: {1}", FindResource("TipLoadCfgSuccess"), openLoadSaveConfigFileDialog.FileName), "LoadCfgFromFile Success");
                    return ByteUtils.FromHex(cfgStr.Replace(" ", "").ToString());
                }
                else
                {
                    MessageBox.Show(string.Format("{0}", FindResource("TipWithoutLoadAnyFile")), "LoadCfgFromFile Tips");
                }
            }
            catch (Exception ex)
            {
                MessageBox.Show(string.Format("Load NetCfg: {0}", ex.Message), "LoadCfgFromFile Error");
            }
            return null;
        }

        private void btnLoadCfgFromFile_Click(object sender, EventArgs e)
        {
            try
            {
                byte[] bytes = LoadCfg();
                if (bytes == null)
                {
                    return;
                }
#region NET_COMM
                NET_COMM comm = new NET_COMM(bytes);
                DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, "btnLoadFromFile_Click {0}", comm.ToString());
                //HWConfig
                txtbxHwCfgDeviceName.Text = string.Format("{0}", comm.HWConfig.Modulename);
                txtbxHwCfgMac.Text = string.Format("{0}", comm.HWConfig.DevMAC);
                txtbxHwCfgIp.Text = string.Format("{0}", comm.HWConfig.DevIP);
                txtbxHwCfgMask.Text = string.Format("{0}", comm.HWConfig.DevIPMask);
                txtbxHwCfgGateway.Text = string.Format("{0}", comm.HWConfig.DevGWIP);
                chkbxHwCfgDhcpEn.Checked = comm.HWConfig.DhcpEnable;
                chkbxHwCfgComCfgEn.Checked = comm.HWConfig.ComcfgEn;
                //Port_0
                chkbxPort0PortEn.Checked = comm.PortCfg_0.PortEn;
                txtbxHeartbeatInterval.Text = string.Format("{0}", comm.PortCfg_0.RxPktTimeout);
                txtbxHeartbeatContent.Text = string.Format("{0}", comm.PortCfg_0.Domainname);
                ////Port_1
                chkbxPort1_PortEn.Checked = comm.PortCfg_1.PortEn;
                if (cmbbxPort1_NetMode.Items.Contains((NETPORT_TYPE)comm.PortCfg_1.NetMode))
                {
                    cmbbxPort1_NetMode.SelectedItem = (NETPORT_TYPE)comm.PortCfg_1.NetMode;
                }
                else
                {
                    MessageBox.Show(string.Format("Port1 {0}: {1}", FindResource("tipNotSupport"), cmbbxPort1_NetMode));
                }
                chkbxPort1_RandEn.Checked = comm.PortCfg_1.RandSportFlag;
                txtbxPort1_NetPort.Text = string.Format("{0}", comm.PortCfg_1.NetPort);
                txtbxPort1_DesIp.Text = string.Format("{0}", comm.PortCfg_1.DesIP);
                txtbxPort1_DesPort.Text = string.Format("{0}", comm.PortCfg_1.DesPort);
                if (cmbbxPort1_BaudRate.Items.Contains((NETPORT_Baudrate)comm.PortCfg_1.BaudRate))
                {
                    cmbbxPort1_BaudRate.SelectedItem = (NETPORT_Baudrate)comm.PortCfg_1.BaudRate;
                }
                else
                {
                    MessageBox.Show(string.Format("{0} BaudRate {1}", FindResource("tipNotSupport"), comm.PortCfg_1.BaudRate));
                    return;
                }

                if (cmbbxPort1_DataSize.Items.Contains((NETPORT_DataSize)comm.PortCfg_1.DataSize))
                {
                    cmbbxPort1_DataSize.SelectedItem = (NETPORT_DataSize)comm.PortCfg_1.DataSize;
                }
                else
                {
                    MessageBox.Show(string.Format("{0} DataSize {1}", FindResource("tipNotSupport"), comm.PortCfg_1.DataSize));
                    return;
                }

                if (cmbbxPort1_StopBits.Items.Contains((NETPORT_StopBits)comm.PortCfg_1.StopBits))
                {
                    cmbbxPort1_StopBits.SelectedItem = (NETPORT_StopBits)comm.PortCfg_1.StopBits;
                }
                else
                {
                    MessageBox.Show(string.Format("{0} StopBits {1}", FindResource("tipNotSupport"), comm.PortCfg_1.StopBits));
                    return;
                }

                if (cmbbxPort1_Parity.Items.Contains((NETPORT_Parity)comm.PortCfg_1.Parity))
                {
                    cmbbxPort1_Parity.SelectedItem = (NETPORT_Parity)comm.PortCfg_1.Parity;
                }
                else
                {
                    MessageBox.Show(string.Format("{0} Parity {1}", FindResource("tipNotSupport"), comm.PortCfg_1.Parity));
                    return;
                }
                chkbxPort1_PhyDisconnect.Checked = comm.PortCfg_1.PHYChangeHandle;
                txtbxPort1_RxPkgLen.Text = string.Format("{0}", comm.PortCfg_1.RxPktlength);
                txtbxPort1_RxTimeout.Text = string.Format("{0}", comm.PortCfg_1.RxPktTimeout);
                txtbxPort1_ReConnectCnt.Text = string.Format("{0}", comm.PortCfg_1.ReConnectCnt);
                chkbxPort1_ResetCtrl.Checked = comm.PortCfg_1.ResetCtrl;
                txtbxPort1_DnsDomain.Text = string.Format("{0}", comm.PortCfg_1.Domainname);
                txtbxPort1_DnsIp.Text = string.Format("{0}", comm.PortCfg_1.DNSHostIP);
                txtbxPort1_Dnsport.Text = string.Format("{0}", comm.PortCfg_1.DNSHostPort);
#endregion //NET_COMM
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }



        private void btnStoreCfgToFile_Click(object sender, EventArgs e)
        {
            try
            {
                string dev_mac = string.Format("{0}", txtbxHwCfgMac.Text);
                string pc_mac = string.Format("{0}", lblCurPcMac.Text);
                NET_COMM comm = new NET_COMM();
                comm.InitSaveToFile(dev_mac, pc_mac);
                //comm.Flag = "";
                //comm.Cmd = NET_CMD.NET_MODULE_RESERVE;
                //comm.DevMac = "";
                //comm.PcMac = "";
                //comm.Len = "";

#region HWCfg
                comm.HWConfig.DevType = 0x21;
                comm.HWConfig.AuxDevType = 0x21;
                comm.HWConfig.Index = 0x01;
                comm.HWConfig.DevHardwareVer = 0x02;
                comm.HWConfig.DevSoftwareVer = 0x06;
                comm.HWConfig.Modulename = txtbxHwCfgDeviceName.Text.Trim();
                comm.HWConfig.DevMAC = txtbxHwCfgMac.Text.Trim();
                comm.HWConfig.DevIP = txtbxHwCfgIp.Text.Trim();
                comm.HWConfig.DevGWIP = txtbxHwCfgGateway.Text.Trim();
                comm.HWConfig.DevIPMask = txtbxHwCfgMask.Text.Trim();
                comm.HWConfig.DhcpEnable = (chkbxHwCfgDhcpEn.Checked == true ? true : false);
                comm.HWConfig.WebPort = 80;
                comm.HWConfig.Username = "admin";
                comm.HWConfig.PassWordEn = false;
                comm.HWConfig.PassWord = "";
                comm.HWConfig.UpdateFlag = false;
                comm.HWConfig.ComcfgEn = (chkbxHwCfgComCfgEn.Checked == true ? true : false);
                comm.HWConfig.Reserved = "";
#endregion HWCfg

#region Port_0
                comm.PortCfg_0.Index = 0;
                comm.PortCfg_0.PortEn = (chkbxPort0PortEn.Checked == true ? true : false);
                comm.PortCfg_0.NetMode = NETPORT_TYPE.UDP_SERVER;
                comm.PortCfg_0.RandSportFlag = true;
                comm.PortCfg_0.NetPort = 3000;
                comm.PortCfg_0.DesIP = "192.168.1.100";
                comm.PortCfg_0.DesPort = 2000;
                comm.PortCfg_0.BaudRate = NETPORT_Baudrate.B9600;
                comm.PortCfg_0.DataSize = NETPORT_DataSize.Bits8;
                comm.PortCfg_0.StopBits = NETPORT_StopBits.One;
                comm.PortCfg_0.Parity = NETPORT_Parity.None;
                comm.PortCfg_0.PHYChangeHandle = true;
                comm.PortCfg_0.RxPktlength = 1024;
                comm.PortCfg_0.RxPktTimeout = Convert.ToInt32(txtbxHeartbeatInterval.Text);
                comm.PortCfg_0.ReConnectCnt = 0;
                comm.PortCfg_0.ResetCtrl = false;
                comm.PortCfg_0.DNSFlag = false;
                comm.PortCfg_0.Domainname = string.Format("{0}", txtbxHeartbeatContent.Text.Trim());
                comm.PortCfg_0.DNSHostIP = "0.0.0.0";
                comm.PortCfg_0.DNSHostPort = 0;
                comm.PortCfg_0.Reserved = "";
#endregion Port_0

#region Port_1
                comm.PortCfg_1.Index = 1;
                comm.PortCfg_1.PortEn = (chkbxPort1_PortEn.Checked == true ? true : false);
                comm.PortCfg_1.NetMode = (NETPORT_TYPE)cmbbxPort1_NetMode.SelectedIndex;
                comm.PortCfg_1.RandSportFlag = (chkbxPort1_RandEn.Checked == true ? true : false); ;
                comm.PortCfg_1.NetPort = Convert.ToInt32(txtbxPort1_NetPort.Text.Trim());
                comm.PortCfg_1.DesIP = txtbxPort1_DesIp.Text.Trim();
                comm.PortCfg_1.DesPort = Convert.ToInt32(txtbxPort1_DesPort.Text.Trim());
                comm.PortCfg_1.BaudRate = (NETPORT_Baudrate)cmbbxPort1_BaudRate.SelectedIndex;
                comm.PortCfg_1.DataSize = (NETPORT_DataSize)cmbbxPort1_DataSize.SelectedIndex;
                comm.PortCfg_1.StopBits = (NETPORT_StopBits)cmbbxPort1_StopBits.SelectedIndex;
                comm.PortCfg_1.Parity = (NETPORT_Parity)cmbbxPort1_Parity.SelectedIndex;
                comm.PortCfg_1.PHYChangeHandle = (chkbxPort1_PhyDisconnect.Checked == true ? true : false); ;
                comm.PortCfg_1.RxPktlength = Convert.ToInt32(txtbxPort1_RxPkgLen.Text.Trim());
                comm.PortCfg_1.RxPktTimeout = Convert.ToInt32(txtbxPort1_RxTimeout.Text.Trim());
                comm.PortCfg_1.ReConnectCnt = Convert.ToInt32(txtbxPort1_ReConnectCnt.Text.Trim());
                comm.PortCfg_1.ResetCtrl = (chkbxPort1_ResetCtrl.Checked == true ? true : false); ;
                comm.PortCfg_1.DNSFlag = false;
                comm.PortCfg_1.Domainname = string.Format("{0}", txtbxPort1_DnsDomain.Text.Trim());
                comm.PortCfg_1.DNSHostIP = txtbxPort1_DnsIp.Text.Trim();
                comm.PortCfg_1.DNSHostPort = Convert.ToInt32(txtbxPort1_Dnsport.Text.Trim());
                comm.PortCfg_1.Reserved = "";
#endregion Port_1

                System.Windows.Forms.SaveFileDialog saveFileDialog1 = new System.Windows.Forms.SaveFileDialog();
                saveFileDialog1.Filter = "NetPortConfigure (.cfg)|*.cfg";
                saveFileDialog1.Title = string.Format("{0}", FindResource("TipSaveNetPortCfgFile"));
                string strDestinationFile = "NetPortConfigure"
                    + DateTime.Now.ToString("yyyy-MM-dd-HH-mm-ss") + @".cfg";
                saveFileDialog1.FileName = strDestinationFile;
                //saveFileDialog1.InitialDirectory = "D://";
                saveFileDialog1.InitialDirectory = string.Format("{0}", Directory.GetParent(System.Reflection.Assembly.GetExecutingAssembly().Location));
                // If the user clicked OK in the dialog and
                // a .txt file was selected, open it.
                if (saveFileDialog1.ShowDialog() == System.Windows.Forms.DialogResult.OK)
                {
                    string path = saveFileDialog1.FileName;// Application.StartupPath + @"\" + comm.Flag + ".cfg";
                    StreamWriter sWriter = File.CreateText(path);
                    //sWriter.Write(ByteUtils.ToHex(comm.Bytes, "", " "));
                    for (int i = 0; i < comm.Bytes.Length; i++)
                    {
                        sWriter.Write("{0:x2} ", comm.Bytes[i]);
                        if ((i + 1) % 20 == 0)
                            sWriter.WriteLine();
                    }
                    sWriter.Flush();
                    sWriter.Close();
                    MessageBox.Show(string.Format("{0}: store to: {1}", FindResource("TipStoreCfgToFileSuccess"), path), "StoreCfgToFile Success");
                }
                else
                {
                    MessageBox.Show(string.Format("{0}", FindResource("TipWithoutSaveAnyFile")), "StoreCfgToFile Tips");
                }
            }
            catch (Exception ex)
            {
                OnLog(ex);
            }
        }

        private string tmplrtxt = null;

        private void PrintTransportLog(object sender, MessageTransportEventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                if (m_bDisplayLog == true)
                {
                    string strLog = string.Format("{0:5}: {1}", (e.Tx ? "Send" : "Recv"), ByteUtils.ToHex(e.TransportData, "", " "));
                    HistoryType flag = (e.Tx ? HistoryType.Success : HistoryType.Failed);
                    WriteLog(lrtxtDataTran, strLog, flag);
                }

            }));
 
    

        }


        private void Reader_MessageReadWhenInventory(object sender, MessageReadWhenInventoryEventArgs e)
        {
            CommunicateFlag = true;
            RecordOpHistory(HistoryType.Normal, string.Format("{0}", e.Msg.RawData));
        }

        private void Reader_ExceptionReceived(object sender, ExceptionReceivedEventArgs e)
        {
            BeginInvoke(new ThreadStart(delegate ()
            {
                if (e.Exception is ReaderCodeException)
                {
                    ReaderCodeException rce = (ReaderCodeException)e.Exception;
                    if (rce.Code == ErrorCode.INVENTORY_EXECUTETIME_OVER)
                    {
                        LimitFlag = true;
                        btnInventory_Click_1(null, null);
                        LimitFlag = false;
                    }
                    string tmp = null;
                    switch (rce.Code)
                    {
                        case ErrorCode.TAG_INVENTORY_ERROR:
                            tmp = "Error occurred during inventory";
                            break;
                        case ErrorCode.TAG_READ_ERROR:
                            tmp = "Error occurred during read";
                            break;
                        case ErrorCode.TAG_WRITE_ERROR:
                            tmp = "Error occurred during write";
                            break;
                        case ErrorCode.TAG_LOCK_ERROR:
                            tmp = "Error occurred during lock";
                            break;
                        case ErrorCode.TAG_KILL_ERROR:
                            tmp = "Error occurred during kill";
                            break;
                        case ErrorCode.NO_TAG_ERROR:
                            tmp = "There is no tag to be operated";
                            break;
                        case ErrorCode.INVENTORY_OK_BUT_ACCESS_FAIL:
                            tmp = "Tag Inventoried but access failed";
                            break;
                        case ErrorCode.ACCESS_OR_PASSWORD_ERROR:
                            tmp = "Access failed or wrong password";
                            break;
                        case ErrorCode.PARAMETER_INVALID:
                            tmp = "Invalid parameter";
                            break;
                        case ErrorCode.PARAMETER_INVALID_WORDCNT_TOO_LONG:
                            tmp = "WordCnt is too long";
                            break;
                        case ErrorCode.PARAMETER_INVALID_MEMBANK_OUT_OF_RANGE:
                            tmp = "MemBank out of range";
                            break;
                        case ErrorCode.PARAMETER_INVALID_LOCK_REGION_OUT_OF_RANGE:
                            tmp = "Lock region out of range";
                            break;
                        case ErrorCode.PARAMETER_INVALID_LOCK_ACTION_OUT_OF_RANGE:
                            tmp = "LockType out of range";
                            break;
                        case ErrorCode.PARAMETER_EPC_MATCH_LEN_TOO_LONG:
                            tmp = "EPC match is too long";
                            break;
                        case ErrorCode.PARAMETER_EPC_MATCH_LEN_ERROR:
                            tmp = "EPC match length wrong";
                            break;
                        case ErrorCode.PARAMETER_INVALID_EPC_MATCH_MODE:
                            tmp = "Invalid EPC match mode";
                            break;
                        case ErrorCode.PARAMETER_INVALID_FREQUENCY_RANGE:
                            tmp = "Invalid frequency range";
                            break;
                        case ErrorCode.FAIL_TO_GET_RN16_FROM_TAG:
                            tmp = "Failed to receive RN16 from tag";
                            break;
                        case ErrorCode.PARAMETER_INVALID_DRM_MODE:
                            tmp = "Invalid DRM mode";
                            break;
                        case ErrorCode.PLL_LOCK_FAIL:
                            tmp = "PLL can not lock";
                            break;
                        case ErrorCode.RF_CHIP_FAIL_TO_RESPONSE:
                            tmp = "No response from RF chip";
                            break;
                        case ErrorCode.ANTENNA_MISSING_ERROR:
                            tmp = e.Exception.Message.Substring(50) + "Antenna Disconnect";
                            if (!reader.IsInventorying() && !reader.IsReading())
                            {
                                closeLog();
                                reader.TagRead -= Reader_TagRead;
                                reader.ReadTagCountCallback -= Reader_ReadTagCountCallback;
                                reader.CommandStatistics -= Reader_CommandStatistics;
                                btnInventory.Text = string.Format("{0}", FindResource("StartInventory"));
                            }
                            break;
                        case ErrorCode.COMMAND_FAIL:
                            tmp = "Model Disconnect";
                            if (btnInventory.Text.Equals(FindResource("StopInventory")))
                            {
                                reader.StopReading();
                                dispatcherTimer.Stop();
                                readratePerSecond.Stop();
                                closeLog();
                                reader.TagRead -= Reader_TagRead;
                                reader.ReadTagCountCallback -= Reader_ReadTagCountCallback;
                                reader.CommandStatistics -= Reader_CommandStatistics;
                                btnInventory.Text = string.Format("{0}", FindResource("StartInventory"));
                            }
                            break;
                        default:
                            break;
                    }
                    RecordOpHistory(HistoryType.Failed, tmp);
                    if (readingJohar)
                    {
                        reader.ReadTagJohar();
                    }
                    if (MulAntReadTag)
                    {
                        if (StopMulAntReadTag) return;
                        MulAntTag++;
                        if (MulAntTag >= (int)channels) MulAntTag = 0;
                        reader.SetWorkAntenna((Antenna)MulAntTag);
                    }
                }
            }));

        } 

        private void Reader_CommandStatistics(object sender, CommandstatisticsEventArgs e)
        {
            CommunicateFlag = true;
            this.BeginInvoke(new ThreadStart(delegate ()
            {
                lock (tagdb)
                {
                    txtCmdTagCount.Text = string.Format("{0}", e.RoundTotalRead);
                    led_cmd_readrate.Text = string.Format("{0}", e.RoundReadRate);
                    led_cmd_execute_duration.Text = string.Format("{0}", e.RoundCommandDuration);
                    tagdb.UpdateTotalDuration(e.RoundCommandDuration);

                    if (transportLogFile != null)
                    {
                        transportLogFile.Write(string.Format("[{0}] {1:d5}, {2} {3:d4} ms,[{4}], {5} {6}: {7:d4}, {8}:{9}",
                                DateTime.Now.ToString("MM/dd/yyyy hh:mm:ss.fff tt"),
                                inventory_times,
                                FindResource("tipSpendTime"),
                                (e.RoundCommandDuration + DelayTime),
                                FindResource("tipAntGroup") + (useAntG1 ? "1" : "2"),
                                (ReverseTarget ? ("useTarget" + (invTargetB ? "B," : "A,")) : ""),
                                FindResource("tipTotalCount"),
                                tagdbTmp.TotalReadCounts,
                                FindResource("tipUniqueCount"),
                                tagdbTmp.UniqueTagCounts));
                        transportLogFile.WriteLine();
                        transportLogFile.Flush();
                    }
                    inventory_times++;
                    if(tagdbTmp != null)
                    {
                        tagdbTmp.Clear();
                    }

                    if (LimitFlag)
                    {
                        btnInventory_Click_1(null, null);
                        LimitFlag = false;
                    }

                    if(OATime != null)
                    {
                        OATime.Start();
                    }

                    if (!reader.IsInventorying() && !reader.IsReading())
                    {
                        closeLog();
                        reader.TagRead -= Reader_TagRead;
                        reader.ReadTagCountCallback -= Reader_ReadTagCountCallback;
                        reader.CommandStatistics -= Reader_CommandStatistics;
                        btnInventory.Text = string.Format("{0}", FindResource("StartInventory"));
                    }
                }
            }));
        }

        public class UDPThread
        {
            //UDP Client
            UdpClient netClient = null;
            //Local port, which is used to bind a UDP server
            IPEndPoint localEndpoint = null;
            //Network port, used to hold UDP broadcast addresses
            IPEndPoint netEndpoint = null;
            //UDP Recv Thread
            Thread netRecvthread = null;
            private bool netStarted = false;
            //Wait for UDP to finish receiving
            ManualResetEvent waitForStopRecv = new ManualResetEvent(false);
            //Wait for the Get or Set instruction to return
            //ManualResetEvent waitForGetAndSetAck = new ManualResetEvent(false);
            //private bool startRecvUdp = false;

            //The network card currently used as a UDP service
            NetCard curNetCard = null;

            public event EventHandler<NetCommEventArgs> NetCommRead;

            public NetCard CurNetCard
            {
                get { return curNetCard; }
                set { curNetCard = value; }
            }

            public bool IsStartRead { get { return netStarted; } }

            public UDPThread()
            {

            }

            //Start the UDP service
            private bool StartUdp()
            {
                try
                {
                    if (curNetCard == null)
                    {
                        return false;
                    }
                    if (localEndpoint == null)
                    {
                        localEndpoint = new IPEndPoint(IPAddress.Parse(curNetCard.Ip), 60000);
                    }
                    if (netClient == null)
                    {
                        netClient = new UdpClient();
                        Socket updSocket = new Socket(AddressFamily.InterNetwork, SocketType.Dgram, ProtocolType.Udp);
                        //Reuse must first than Bind
                        updSocket.SetSocketOption(SocketOptionLevel.Socket, SocketOptionName.ReuseAddress, 1);
                        updSocket.Bind(localEndpoint);
                        netClient.Client = updSocket;
                        netClient.Client.SendTimeout = 5000;
                        netClient.Client.ReceiveTimeout = 5000;
                        netClient.Client.ReceiveBufferSize = 2 * 1024;
                    }
                    if (netEndpoint == null)
                    {
                        netEndpoint = new IPEndPoint(IPAddress.Parse("255.255.255.255"), 50000); // Destination address information, broadcast address
                    }

                    if (netRecvthread == null)
                    {
                        netRecvthread = new Thread(new ThreadStart(StartRecvNetPort));
                        netRecvthread.IsBackground = true;
                        netRecvthread.Start();
                    }
                    return true;
                }
                catch (Exception ex)
                {
                    throw ex;
                }
            }

            //Stop UDP service
            private bool StopUdp()
            {
                try
                {
                    if (netStarted)
                    {
                        netStarted = false;
                        waitForStopRecv.Reset();
                        waitForStopRecv.WaitOne();
                    }
                    netRecvthread = null;
                    localEndpoint = null;
                    netEndpoint = null;

                    if (netClient != null)
                    {
                        netClient.Close();
                        netClient = null;
                    }
                    return true;
                }
                catch (Exception ex)
                {
                    throw ex;
                }
            }

            public void RestartUDP()
            {
                try
                {
                    StopUdp();
                    StartUdp();
                }
                catch (Exception ex)
                {
                    throw ex;
                }
            }
            //UDP Recv
            private void StartRecvNetPort()
            {
                netStarted = true;
                while (netStarted)
                {
                    if (/*startRecvUdp ||*/ netClient.Available > 0)
                    {
                        try
                        {
                            IPEndPoint iPEnd = new IPEndPoint(IPAddress.Any, 50000);
                            byte[] buf = netClient.Receive(ref iPEnd);
                            string msg = ByteUtils.ToHex(buf, "", " ");
                            //DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG,"#2 Recv:{0}", msg);
                            parseNetComm(buf);
                        }
                        catch (SocketException e)
                        {
                            MessageBox.Show(string.Format("Recv timeout"), "NetPort operation");
                            //startRecvUdp = false;
                            //waitForGetAndSetAck.Set();
                        }
                    }
                    Thread.Sleep(10);
                }
                //startRecvUdp = false;
                waitForStopRecv.Set();
            }

            //Parse NetComm message
            private void parseNetComm(byte[] buf)
            {
                NET_COMM comm = new NET_COMM(buf);
                if (comm.Cmd == NET_CMD.NET_MODULE_ACK_SEARCH)
                {

                }
                if (comm.Cmd == NET_CMD.NET_MODULE_ACK_RESEST)
                {
                    //waitForGetAndSetAck.Set();
                }
                if (comm.Cmd == NET_CMD.NET_MODULE_ACK_GET
                    | comm.Cmd == NET_CMD.NET_MODULE_ACK_SET)
                {
                    //waitForGetAndSetAck.Set();
                }
                OnThresholdReached(new NetCommEventArgs(comm));
            }

            protected virtual void OnThresholdReached(NetCommEventArgs e)
            {
                EventHandler<NetCommEventArgs> handler = NetCommRead;
                if (handler != null)
                {
                    handler(this, e);
                }
            }

            // Send NetComm Message
            private void SendNetPortMessage(byte[] sendData)
            {
                try
                {
                    if (netClient != null && netStarted)
                        netClient.Send(sendData, sendData.Length, netEndpoint);
                }
                catch (Exception ex)
                {
                    throw ex;
                }
            }

            public bool StartSearchNetPort()
            {
                try
                {
                    if (!StartUdp())
                    {
                        return false;
                    }
                    NET_COMM comm = new NET_COMM();
                    SendNetPortMessage(comm.InitDevSearch());
                    return true;
                }
                catch (Exception ex)
                {
                    throw ex;
                }
            }

            public bool StopSearchNetPort()
            {
                try
                {
                    return StopUdp();
                }
                catch (Exception ex)
                {
                    throw ex;
                }
            }

            public void GetNetPort(NetPortDevice npd)
            {
                try
                {
                    if (!StartUdp())
                    {
                        return;
                    }
                    Console.WriteLine("GetNetPort {0}", npd.DeviceMac);
                    NET_COMM comm = new NET_COMM();
                    SendNetPortMessage(comm.InitDevGet(npd.DeviceMac));
                }
                catch (Exception ex)
                {
                    throw ex;
                }
            }

            public void SetNetPort(NetPortDevice npd, string pc_mac, DeviceHWConfig hwCfg, DevicePortConfig[] portCfg)
            {
                try
                {
                    StartUdp();
                    Console.WriteLine("SetNetPort {0}, pc_mac={1}", npd.DeviceMac, pc_mac);
                    NET_COMM comm = new NET_COMM();
                    SendNetPortMessage(comm.InitDevSet(npd.DeviceMac, pc_mac, hwCfg, portCfg));
                }
                catch (Exception ex)
                {
                    throw ex;
                }
            }

            public void ResetNetPort(NetPortDevice npd)
            {
                try
                {
                    StartUdp();
                    Console.WriteLine("GetNetPort {0}", npd.DeviceMac);
                    NET_COMM comm = new NET_COMM();
                    SendNetPortMessage(comm.InitDevReset(npd.DeviceMac));
                }
                catch (Exception ex)
                {
                    throw ex;
                }
            }

            public void DefaultNetPort(NetPortDevice npd, string pcMac)
            {
                try
                {
                    StartUdp();
                    Console.WriteLine("GetNetPort {0}", npd.DeviceMac);
                    NET_COMM comm = new NET_COMM();
                    SendNetPortMessage(comm.InitDefault(npd.DeviceMac, pcMac));
                }
                catch (Exception ex)
                {
                    throw ex;
                }
            }
        }

        private void btGetProfile_Click(object sender, EventArgs e)
        {
            RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipGetProfile")));
            reader.GetRfLinkProfile();
        }

        private void btSetProfile_Click(object sender, EventArgs e)
        {
            RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipSetProfile")));
            reader.SetRfLinkProfile(cmbModuleLink.SelectedIndex);
        }

        private void btGetE710Profile_Click(object sender, EventArgs e)
        {
            RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipE710GetProfile")));
            reader.E710GetRfLinkProfile();
        }

        private void btSetE710Profile_Click(object sender, EventArgs e)
        {
            byte[] data = new byte[2];
            data[0] = (byte)cbbE710RfLink.SelectedIndex;
            data[1] = (byte)(cbDrmSwich.Checked ? 1 : 0);
            E710Profile profile = new E710Profile(data);
            RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipE710SetProfile")));
            reader.E710SetRfLinkProfile(profile);
        }

        private void btGetQValue_Click(object sender, EventArgs e)
        {
            RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipE710GetQValue")));
            reader.E710GetQConfig();
        }

        private void btSetQValue_Click(object sender, EventArgs e)
        {
            RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipE710SetQValue")));
            if (rbDyQ.Checked)
            {
                byte[] data = new byte[6];
                data[0] = 1;
                data[1] = (byte)cbbInitQValue.SelectedIndex;
                data[2] = (byte)cbbMaxQValue.SelectedIndex;
                data[3] = (byte)cbbMinQValue.SelectedIndex;
                data[4] = byte.Parse(tbNumMinQ.Text.Trim());
                data[5] = byte.Parse(tbMaxQSince.Text.Trim());
                Q_Config q_Config = new Q_Config(data);
                reader.E710SetQConfig(q_Config);
            }

            if (rbStQ.Checked)
            {
                byte[] data = new byte[4];
                data[0] = 0;
                data[1] = (byte)cbbInitQValue.SelectedIndex;
                data[2] = (byte)cbbMaxQValue.SelectedIndex;
                data[3] = (byte)cbbMinQValue.SelectedIndex;
                Q_Config q_Config = new Q_Config(data);
                reader.E710SetQConfig(q_Config);
            }


        }

        private void QType_CheckedChanged(object sender, EventArgs e)
        {
            if (rbDyQ.Checked)
            {
                label44.Enabled = true;
                tbNumMinQ.Enabled = true;
                label45.Enabled = true;
                tbMaxQSince.Enabled = true;
            }

            if(rbStQ.Checked)
            {
                label44.Enabled = false;
                tbNumMinQ.Enabled = false;
                label45.Enabled = false;
                tbMaxQSince.Enabled = false;
            }
        }

        private void btE710Refresh_Click(object sender, EventArgs e)
        {
            rbDyQ.Checked = false;
            rbStQ.Checked = false;

            cbbE710RfLink.SelectedIndex = -1;
            cbbInitQValue.SelectedIndex = -1;
            cbbMaxQValue.SelectedIndex = -1;
            cbbMinQValue.SelectedIndex = -1;

            tbMaxQSince.Text = "";
            tbNumMinQ.Text = "";

            cbDrmSwich.Checked = false;
        }

        private void ModelR2000_CheckedChanged(object sender, EventArgs e)
        {
            if (rb_R2000.Checked)
            {
                gbProfile.Visible = true;
                this.tabControl_baseSettings.TabPages.Remove(this.tabPage4);
                cmbSetBaudrate.Items.Clear();
                cmbBaudrate.Items.Clear();
                for(int i = 0; i < BaudRateR2000.Length; i++)
                {
                    cmbBaudrate.Items.Add(BaudRateR2000[i]);
                    cmbSetBaudrate.Items.Add(BaudRateR2000[i]);
                }
                rb_fast_inv.Visible = false;
                cmbBaudrate.SelectedIndex = 1; //115200
            }
        }

        private void ModelE710_CheckedChanged(object sender, EventArgs e)
        {
            if (rb_E710.Checked)
            {
                gbProfile.Visible = false;
                this.tabControl_baseSettings.TabPages.Add(this.tabPage4); 
                cmbSetBaudrate.Items.Clear();
                cmbBaudrate.Items.Clear();
                for (int i = 0; i < BaudRateE710.Length; i++)
                {
                    cmbBaudrate.Items.Add(BaudRateE710[i]);
                    cmbSetBaudrate.Items.Add(BaudRateE710[i]);
                }
                rb_fast_inv.Visible = true;
                cmbBaudrate.SelectedIndex = 1; //115200
            }
        }

        private void cb_IceBoxTest_CheckedChanged(object sender, EventArgs e)
        {
            if (cb_IceBoxTest.Checked)
            {
                IceTest = true;
            }
            else
            {
                IceTest = false;
            }
        }

        private void cb_InvTime_CheckedChanged(object sender, EventArgs e)
        {
            if (cb_InvTime.Checked)
            {
                mInventoryExeCount.Text = "-1";
                mFastIntervalTime.Text = "0";
                mFastIntervalTime.Enabled = false;
                mInventoryExeCount.Enabled = false;
            }
            else
            {
                mFastIntervalTime.Enabled = true;
                mInventoryExeCount.Enabled = true;
            }
        }

        private void tb_outputpower_9_TextChanged(object sender, EventArgs e)
        {
            if (!CheckPower(tb_outputpower_9.Text))
            {
                tb_outputpower_9.Text = "";
                return;
            }
        }

        private void tb_outputpower_10_TextChanged(object sender, EventArgs e)
        {
            if (!CheckPower(tb_outputpower_10.Text))
            {
                tb_outputpower_10.Text = "";
                return;
            }
        }

        private void tb_outputpower_11_TextChanged(object sender, EventArgs e)
        {
            if (!CheckPower(tb_outputpower_11.Text))
            {
                tb_outputpower_11.Text = "";
                return;
            }
        }

        private void tb_outputpower_12_TextChanged(object sender, EventArgs e)
        {
            if (!CheckPower(tb_outputpower_12.Text))
            {
                tb_outputpower_12.Text = "";
                return;
            }
        }

        private void tb_outputpower_13_TextChanged(object sender, EventArgs e)
        {
            if (!CheckPower(tb_outputpower_13.Text))
            {
                tb_outputpower_13.Text = "";
                return;
            }
        }

        private void tb_outputpower_14_TextChanged(object sender, EventArgs e)
        {
            if (!CheckPower(tb_outputpower_14.Text))
            {
                tb_outputpower_14.Text = "";
                return;
            }
        }

        private void tb_outputpower_15_TextChanged(object sender, EventArgs e)
        {
            if (!CheckPower(tb_outputpower_15.Text))
            {
                tb_outputpower_15.Text = "";
                return;
            }
        }

        private void tb_outputpower_16_TextChanged(object sender, EventArgs e)
        {
            if (!CheckPower(tb_outputpower_16.Text))
            {
                tb_outputpower_16.Text = "";
                return;
            }
        }

        private void btGetTm600Profile_Click(object sender, EventArgs e)
        {
            reader.GetTm600RfLinkProfile();
            RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipTm600SetProfile")));
        }

        private void btSetTm600Profile_Click(object sender, EventArgs e)
        {
            byte data = (byte)cbbTm600RFLink.SelectedIndex;
            RecordOpHistory(HistoryType.Normal, string.Format("{0}", FindResource("tipTm600SetProfile")));
            reader.SetTm600RfLinkProfile(data);
        }


        private byte Gopid;
        private int Gtestcnt = 0;
        private string Gdata;
        private int Grepeat = 0;
        private System.Timers.Timer DelayTimeCmd;
        private bool StartTestFlag = false;
        private void btnSerialTest_Click(object sender, EventArgs e)
        {
            if (btnSerialTest.Text.Equals("启动测试"))
            {
                lbPCSendCnt.Text = "0";
                lbPCRecCnt.Text = "0";
                lbPCTestTimeCnt.Text = "0";
                lbModelSendCnt.Text = "0";
                lbModelRevCnt.Text = "0";
                lbModelTestTimeCnt.Text = "0";
                Gtestcnt = 0;
                Grepeat = 0;
                GtestRecCnt = 0;

                byte opid = (byte)cbbTestModel.SelectedIndex;
                int repeat = Convert.ToInt32(tbTestCnt.Text.Trim());
                int len = Convert.ToInt32(tbCmdLen.Text.Trim());
                int peroid = Convert.ToInt32(tbSendPeroid.Text.Trim());
                Gopid = opid;
                Gdata = tbTestCmd.Text.Trim();
                Grepeat = repeat;

                if(Gdata.Length < len * 2)
                {
                    MessageBox.Show("长度不够");
                    return;
                }

                if(peroid < 10)
                {
                    MessageBox.Show("周期需要10的倍数");
                    return;
                }
                TestData = ByteUtils.FromHex(Gdata);

                if (cbSendPeroid.Checked)
                {
                    if (null != E710CmdTimer)
                    {
                        E710CmdTimer.Stop();
                        E710CmdTimer = null;
                    }

                    E710CmdTimer = new System.Timers.Timer();
                    E710CmdTimer.Interval = peroid;
                    E710CmdTimer.Elapsed += E710CmdTimer_Elapsed;
                }

                if(null != DelayTimeCmd)
                {
                    DelayTimeCmd.Stop();
                    DelayTimeCmd = null;
                }
                DelayTimeCmd = new System.Timers.Timer();
                DelayTimeCmd.Interval = 200;
                DelayTimeCmd.Elapsed += DelayTimeCmd_Elapsed;


                reader.E710SetSerailTest(opid, true, len, repeat, (short)peroid);
                StartTestFlag = false;
                DelayTimeCmd.Start();
            }
            else 
            {
                btnSerialTest.Text = "启动测试";
                if (null != E710CmdTimer)
                {
                    E710CmdTimer.Stop();
                    E710CmdTimer = null;
                }
                if (null != DelayTimeCmd)
                {
                    DelayTimeCmd.Stop();
                    DelayTimeCmd = null;
                }
            }
        }

        private void DelayTimeCmd_Elapsed(object sender, System.Timers.ElapsedEventArgs e)
        {
            if(DelayTimeCmd.Enabled)
            {
                if (StartTestFlag)
                {
                    if (Gtestcnt >= Grepeat)
                    {
                        if (null != DelayTimeCmd)
                        {
                            DelayTimeCmd.Stop();
                            DelayTimeCmd = null;
                        }
                        return;
                    }
                    else
                    {
                        DelayTimeCmd.Stop();
                        Gtestcnt++;
                        if (Gtestcnt >= Grepeat)
                        {
                            lbPCSendCnt.Text = String.Format("{0}", Grepeat);
                            return;
                        }
                        reader.E710SerailTestCmd(Gopid, Gtestcnt, TestData, TestData.Length);
                        DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, "超时应答：Gtestcnt = {0}", Gtestcnt);
                        DelayTimeCmd.Start();
                    }
                }
                else
                {
                    if (null != DelayTimeCmd)
                    {
                        DelayTimeCmd.Stop();
                        DelayTimeCmd = null;
                    }
                }
            }
        }

        private void E710CmdTimer_Elapsed(object sender, System.Timers.ElapsedEventArgs e)
        {
            if (E710CmdTimer.Enabled)
            {
                if(Gtestcnt >= Grepeat)
                {
                    if(null != E710CmdTimer)
                    {
                        E710CmdTimer.Stop();
                        E710CmdTimer = null;
                    }
                    return;
                }
                else
                {
                    DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, "定时发送1：Gtestcnt = {0}", Gtestcnt);
                    Gtestcnt++;
                    //DebugLog.GetLogger().log(DebugLevel.LOG_DEBUG, "定时发送2：Gtestcnt = {0}", Gtestcnt);
                    if (Gtestcnt >= Grepeat)
                    {
                        BeginInvoke(new ThreadStart(delegate ()
                        {
                            TimeSpan span = DateTime.Now - startCmdTime;
                            long ts = span.Hours * 60 * 60 * 1000 + span.Minutes * 60 * 1000 + span.Seconds * 1000 + span.Milliseconds;
                            lbPCTestTimeCnt.Text = String.Format("{0}", ts);
                            lbPCSendCnt.Text = String.Format("{0}", Grepeat);
                        }));
                        return;
                    }
                    reader.E710SerailTestCmd(Gopid, Gtestcnt, TestData, TestData.Length);
                    BeginInvoke(new ThreadStart(delegate ()
                    {
                        TimeSpan span = DateTime.Now - startCmdTime;
                        lbPCTestTimeCnt.Text = String.Format("{0}", span.TotalMilliseconds);
                        lbPCSendCnt.Text = String.Format("{0}", Gtestcnt + 1);
                    }));
                }
            }
        }

        private System.Timers.Timer E710CmdTimer = null;

        private void cbbTestModel_SelectedIndexChanged(object sender, EventArgs e)
        {
            switch (cbbTestModel.SelectedIndex)
            {
                case 0:
                case 1:
                    {
                        cbSendPeroid.Checked = true;
                        cbSendPeroid.Enabled = true;
                        tbSendPeroid.Enabled = true;
                    }
                    break;
                case 2:
                case 3:
                    {
                        cbSendPeroid.Checked = false;
                        cbSendPeroid.Enabled = false;
                        tbSendPeroid.Enabled = false;
                    }
                    break;
            }
        }

        private void lLbConfig_LinkClicked(object sender, LinkLabelLinkClickedEventArgs e)
        {
            flowLayoutPanel1.Visible = !flowLayoutPanel1.Visible;


            if (WindowState == FormWindowState.Maximized)
            {
                if (!flowLayoutPanel1.Visible)
                {
                    flowLayoutPanel5.Height = 661;
                }
                else
                {
                    flowLayoutPanel5.Height = 225; 
                }
            }
            else if (WindowState == FormWindowState.Normal)
            {
                if (!flowLayoutPanel1.Visible)
                {
                    flowLayoutPanel5.Height = 331;
                }
                else
                {
                    flowLayoutPanel5.Height = 125;
                }
            }

        }

        private void lLbTagFilter_LinkClicked(object sender, LinkLabelLinkClickedEventArgs e)
        {
            flowLayoutPanel5.Visible = !flowLayoutPanel5.Visible;
            panel14.Visible = !panel14.Visible;


            if (WindowState == FormWindowState.Maximized)
            {
                if (!flowLayoutPanel5.Visible)
                {
                    flowLayoutPanel1.Height = 601;
                    groupBox26.Height = 701;
                    dgvInventoryTagResults.Height = 656;
                }
                else
                {
                    flowLayoutPanel1.Height = 446;
                    groupBox26.Height = 506;
                    dgvInventoryTagResults.Height = 458;
                }
            }
            else if (WindowState == FormWindowState.Normal)
            {
                if (!flowLayoutPanel5.Visible)
                {
                    flowLayoutPanel1.Height = 331;
                    groupBox26.Height = 371;
                    dgvInventoryTagResults.Height = 323;
                }
                else
                {
                    flowLayoutPanel1.Height = 206;
                    groupBox26.Height = 246;
                    dgvInventoryTagResults.Height = 198;
                }
            }

        }

        private void btn_SetFunction_Click(object sender, EventArgs e)
        {
            if (cbb_FunctionId.SelectedIndex == -1)
            {
                MessageBox.Show("Please select a function ID");
                return;
            }
            else
            {
                reader.SetCustomFunctionID((byte)(cbb_FunctionId.SelectedIndex));
                string strCmdLog = "Function ID set ";
                WriteLog(lrtxtLog, strCmdLog, 0);
            }
        }

        private void btn_GetFunction_Click(object sender, EventArgs e)
        {
            reader.GetCustomFunctionID();
        }


        //记录快速轮询天线参数
        private byte[] m_btAryData;

        private void btn_SetAntSwitch_Click(object sender, EventArgs e)
        {
            short antASelection = 1;
            short antBSelection = 1;
            short antCSelection = 1;
            short antDSelection = 1;
            short antESelection = 1;
            short antFSelection = 1;
            short antGSelection = 1;
            short antHSelection = 1;

            FastSwitchAntInventoryCfg cfg = null;
            List<InventoryAntenna> ant = new List<InventoryAntenna>();

            string strException = string.Empty;

            if(channels > Channels.Four)
            {
                m_btAryData = new byte[18];

                for (int i = 0; i < 18; i++)
                {
                    m_btAryData[i] = 0;
                }
            }
            else
            {
                m_btAryData = new byte[10];

                for (int i = 0; i < 10; i++)
                {
                    m_btAryData[i] = 0;
                }
            }

            try
            {
                if ((cmbAntSelect1.SelectedIndex < 0) || (cmbAntSelect1.SelectedIndex > 7))
                {
                    m_btAryData[0] = 0xFF;
                }
                else
                {
                    m_btAryData[0] = Convert.ToByte(cmbAntSelect1.SelectedIndex);
                }
                if (txtAStay.Text.Length == 0)
                {
                    m_btAryData[1] = 0x00;
                }
                else
                {
                    m_btAryData[1] = Convert.ToByte(txtAStay.Text);
                }
                ant.Add(new InventoryAntenna((Antenna)Enum.ToObject(typeof(Antenna), m_btAryData[0]), m_btAryData[1]));

                if ((cmbAntSelect2.SelectedIndex < 0) || (cmbAntSelect2.SelectedIndex > 7))
                {
                    m_btAryData[2] = 0xFF;
                }
                else
                {
                    m_btAryData[2] = Convert.ToByte(cmbAntSelect2.SelectedIndex);
                }
                if (txtBStay.Text.Length == 0)
                {
                    m_btAryData[3] = 0x00;
                }
                else
                {
                    m_btAryData[3] = Convert.ToByte(txtBStay.Text);
                }
                ant.Add(new InventoryAntenna((Antenna)Enum.ToObject(typeof(Antenna), m_btAryData[2]), m_btAryData[3]));

                if ((cmbAntSelect3.SelectedIndex < 0) || (cmbAntSelect3.SelectedIndex > 7))
                {
                    m_btAryData[4] = 0xFF;
                }
                else
                {
                    m_btAryData[4] = Convert.ToByte(cmbAntSelect3.SelectedIndex);
                }
                if (txtCStay.Text.Length == 0)
                {
                    m_btAryData[5] = 0x00;
                }
                else
                {
                    m_btAryData[5] = Convert.ToByte(txtCStay.Text);
                }
                ant.Add(new InventoryAntenna((Antenna)Enum.ToObject(typeof(Antenna), m_btAryData[4]), m_btAryData[5]));

                if ((cmbAntSelect4.SelectedIndex < 0) || (cmbAntSelect4.SelectedIndex > 7))
                {
                    m_btAryData[6] = 0xFF;
                }
                else
                {
                    m_btAryData[6] = Convert.ToByte(cmbAntSelect4.SelectedIndex);
                }
                if (txtDStay.Text.Length == 0)
                {
                    m_btAryData[7] = 0x00;
                }
                else
                {
                    m_btAryData[7] = Convert.ToByte(txtDStay.Text);
                }
                ant.Add(new InventoryAntenna((Antenna)Enum.ToObject(typeof(Antenna), m_btAryData[6]), m_btAryData[7]));

                if(channels > Channels.Four)
                {
                    if ((cmbAntSelect5.SelectedIndex < 0) || (cmbAntSelect5.SelectedIndex > 7))
                    {
                        m_btAryData[8] = 0xFF;
                    }
                    else
                    {
                        m_btAryData[8] = Convert.ToByte(cmbAntSelect5.SelectedIndex);
                    }
                    if (txtEStay.Text.Length == 0)
                    {
                        m_btAryData[9] = 0x00;
                    }
                    else
                    {
                        m_btAryData[9] = Convert.ToByte(txtEStay.Text);
                    }
                    ant.Add(new InventoryAntenna((Antenna)Enum.ToObject(typeof(Antenna), m_btAryData[8]), m_btAryData[9]));

                    if ((cmbAntSelect6.SelectedIndex < 0) || (cmbAntSelect6.SelectedIndex > 7))
                    {
                        m_btAryData[10] = 0xFF;
                    }
                    else
                    {
                        m_btAryData[10] = Convert.ToByte(cmbAntSelect6.SelectedIndex);
                    }
                    if (txtFStay.Text.Length == 0)
                    {
                        m_btAryData[11] = 0x00;
                    }
                    else
                    {
                        m_btAryData[11] = Convert.ToByte(txtFStay.Text);
                    }
                    ant.Add(new InventoryAntenna((Antenna)Enum.ToObject(typeof(Antenna), m_btAryData[10]), m_btAryData[11]));

                    if ((cmbAntSelect7.SelectedIndex < 0) || (cmbAntSelect7.SelectedIndex > 7))
                    {
                        m_btAryData[12] = 0xFF;
                    }
                    else
                    {
                        m_btAryData[12] = Convert.ToByte(cmbAntSelect7.SelectedIndex);
                    }
                    if (txtGStay.Text.Length == 0)
                    {
                        m_btAryData[13] = 0x00;
                    }
                    else
                    {
                        m_btAryData[13] = Convert.ToByte(txtGStay.Text);
                    }
                    ant.Add(new InventoryAntenna((Antenna)Enum.ToObject(typeof(Antenna), m_btAryData[12]), m_btAryData[13]));

                    if ((cmbAntSelect8.SelectedIndex < 0) || (cmbAntSelect8.SelectedIndex > 7))
                    {
                        m_btAryData[14] = 0xFF;
                    }
                    else
                    {
                        m_btAryData[14] = Convert.ToByte(cmbAntSelect8.SelectedIndex);
                    }
                    if (txtHStay.Text.Length == 0)
                    {
                        m_btAryData[15] = 0x00;
                    }
                    else
                    {
                        m_btAryData[15] = Convert.ToByte(txtHStay.Text);
                    }
                    ant.Add(new InventoryAntenna((Antenna)Enum.ToObject(typeof(Antenna), m_btAryData[14]), m_btAryData[15]));

                    if (txtInterval.Text.Length == 0)
                    {
                        m_btAryData[16] = 0x00;
                    }
                    else
                    {
                        m_btAryData[16] = Convert.ToByte(tb_Interval.Text);
                    }


                    if (m_btAryData[8] > 7)
                    {
                        antESelection = 0;
                    }

                    if (m_btAryData[10] > 7)
                    {
                        antFSelection = 0;
                    }

                    if (m_btAryData[12] > 7)
                    {
                        antGSelection = 0;
                    }

                    if (m_btAryData[14] > 7)
                    {
                        antHSelection = 0;
                    }

                    if ((antASelection * m_btAryData[1] + antBSelection * m_btAryData[3]
                            + antCSelection * m_btAryData[5] + antDSelection * m_btAryData[7]
                            + antESelection * m_btAryData[9] + antFSelection * m_btAryData[11]
                            + antGSelection * m_btAryData[13] + antHSelection * m_btAryData[15]) == 0)
                    {
                    MessageBox.Show("Please set one antenna for one round.");

                        return;
                    }

                    cfg = new FastSwitchAntInventoryCfg(ant, m_btAryData[17], 0);

                    reader.setInventoryCfg(cfg);


                    reader.SetAntSequence(m_btAryData);

                }
                else
                {
                    if (txtInterval.Text.Length == 0)
                    {
                        m_btAryData[8] = 0x00;
                    }
                    else
                    {
                        m_btAryData[8] = Convert.ToByte(tb_Interval.Text);
                    }

                    if (m_btAryData[0] > 7)
                    {
                        antASelection = 0;
                    }

                    if (m_btAryData[2] > 7)
                    {
                        antBSelection = 0;
                    }

                    if (m_btAryData[4] > 7)
                    {
                        antCSelection = 0;
                    }

                    if (m_btAryData[6] > 7)
                    {
                        antDSelection = 0;
                    }

                    if ((antASelection * m_btAryData[1] + antBSelection * m_btAryData[3]
                        + antCSelection * m_btAryData[5] + antDSelection * m_btAryData[7]) == 0)
                    {
                        MessageBox.Show("请至少选择1个天线设置1次轮询。");

                        return;
                    }

                    cfg = new FastSwitchAntInventoryCfg(ant, m_btAryData[9], 0);

                    reader.setInventoryCfg(cfg);

                    reader.SetAntSequence(m_btAryData);
                }

            }
            catch (System.Exception ex)
            {
                MessageBox.Show(ex.Message);
            }




        }

        private void btn_GetAntSwitch_Click(object sender, EventArgs e)
        {
            reader.GetAntSequence();
        }


        public static int FreqValue = 0;

        private bool FactoryResetFlag = false;

        private void btnFactoryReset_Click(object sender, EventArgs e)
        {
            FactoryResetFlag = true;
            //配置模块频段（欧标、美标）
            btnFactoryReset.Enabled = false;
            FactoryReset factoryReset = new FactoryReset();
            factoryReset.ShowDialog();
            if(factoryReset.DialogResult == DialogResult.OK)
            {
                //设置（欧标或美标）频段
                FrequencyRegion frequencyRegion = new FrequencyRegion();
                switch (FreqValue)
                {
                    case 1:
                        {
                            frequencyRegion.Region = RFID_API_ver1.Region.ETSI;
                            frequencyRegion.StartFreq = 865000;
                            frequencyRegion.EndFreq = 868000;
                        }
                        break;
                    case 2:
                        {
                            frequencyRegion.Region = RFID_API_ver1.Region.FCC;
                            frequencyRegion.StartFreq = 902000;
                            frequencyRegion.EndFreq = 928000;
                        }
                        break;
                }
                reader.SetFrequencyRegion(frequencyRegion);
                SetFormEnable(false);

            }

        }

        private bool FirstOnResize = false;
        protected override void OnResize(EventArgs e)
        {
            base.OnResize(e);
            if (FirstOnResize)
            {
                if (WindowState == FormWindowState.Maximized)
                {
                    if (!flowLayoutPanel1.Visible)
                    {
                        flowLayoutPanel5.Height = 601;
                    }
                    else
                    {
                        flowLayoutPanel5.Height = 225;
                    }

                    if (!flowLayoutPanel5.Visible)
                    {
                        flowLayoutPanel1.Height = 601;
                        groupBox26.Height = 701;
                        dgvInventoryTagResults.Height = 656;
                    }
                    else
                    {
                        flowLayoutPanel1.Height = 466;
                        groupBox26.Height = 506;
                        dgvInventoryTagResults.Height = 458;
                    }
                }
                else if (WindowState == FormWindowState.Normal)
                {
                    flowLayoutPanel1.Height = 206;
                    flowLayoutPanel5.Height = 125;
                }
            }
            else
            {
                FirstOnResize = true;
            }

        }

        private int MulAntTag = 0;
        private void cbMulAnt_CheckedChanged(object sender, EventArgs e)
        {
            if (cbMulAnt.Checked)
            {
                btnReadTag.Text = "开始";
                MulAntReadTag = true;
                reader.GetWorkAntenna();
            }
            else
            {
                MulAntReadTag = false;
                btnReadTag.Text = "读标签";
            }
        }

        private void showSelectedAnt()
        {
            if (channels <= Channels.Four)
            {
                cmbAntSelect5.Enabled = false;
                txtEStay.Enabled = false;
                cmbAntSelect6.Enabled = false;
                txtFStay.Enabled = false;
                cmbAntSelect7.Enabled = false;
                txtGStay.Enabled = false;
                cmbAntSelect8.Enabled = false;
                txtHStay.Enabled = false;
            }
            else
            {
                cmbAntSelect5.Enabled = true;
                txtEStay.Enabled = true;
                cmbAntSelect6.Enabled = true;
                txtFStay.Enabled = true;
                cmbAntSelect7.Enabled = true;
                txtGStay.Enabled = true;
                cmbAntSelect8.Enabled = true;
                txtHStay.Enabled = true;
            }
        }

        private void btn_RefreshSpecial_Click(object sender, EventArgs e)
        {
            cmbAntSelect1.SelectedIndex = 0;
            cmbAntSelect2.SelectedIndex = 1;
            cmbAntSelect3.SelectedIndex = 2;
            cmbAntSelect4.SelectedIndex = 3;
            cmbAntSelect5.SelectedIndex = 4;
            cmbAntSelect6.SelectedIndex = 5;
            cmbAntSelect7.SelectedIndex = 6;
            cmbAntSelect8.SelectedIndex = 7;

            tb_Interval.Text = "0";

            cbb_FunctionId.SelectedIndex = -1;

            txtAStay.Text = "0";
            txtBStay.Text = "0";
            txtCStay.Text = "0";
            txtDStay.Text = "0";
            txtEStay.Text = "0";
            txtFStay.Text = "0";
            txtGStay.Text = "0";
            txtHStay.Text = "0";

        }
    }
}