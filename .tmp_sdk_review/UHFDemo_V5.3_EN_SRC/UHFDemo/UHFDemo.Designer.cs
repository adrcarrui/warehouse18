using System.Windows.Forms;
using System.ComponentModel;

namespace UHFDemo
{
    partial class UHFDemo
    {
        /// <summary>
        /// 必需的设计器变量。
        /// </summary>
        private IContainer components = null;

        // add ms
        public static long wasteTime = 0;

        /// <summary>
        /// 清理所有正在使用的资源。
        /// </summary>
        /// <param name="disposing">如果应释放托管资源，为 true；否则为 false。</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows 窗体设计器生成的代码
        /// <summary>
        /// 设计器支持所需的方法 - 不要
        /// 使用代码编辑器修改此方法的内容。
        /// </summary>
        private void InitializeComponent()
        {
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(UHFDemo));
            this.tabCtrMain = new System.Windows.Forms.TabControl();
            this.PagReaderSetting = new System.Windows.Forms.TabPage();
            this.tabControl_baseSettings = new System.Windows.Forms.TabControl();
            this.tabPage1 = new System.Windows.Forms.TabPage();
            this.btnFactoryReset = new System.Windows.Forms.Button();
            this.flowLayoutPanel2 = new System.Windows.Forms.FlowLayoutPanel();
            this.gbModel = new System.Windows.Forms.GroupBox();
            this.rb_E710 = new System.Windows.Forms.RadioButton();
            this.rb_R2000 = new System.Windows.Forms.RadioButton();
            this.groupBox1 = new System.Windows.Forms.GroupBox();
            this.btnConnect = new System.Windows.Forms.Button();
            this.groupBox24 = new System.Windows.Forms.GroupBox();
            this.antType16 = new System.Windows.Forms.RadioButton();
            this.antType8 = new System.Windows.Forms.RadioButton();
            this.antType4 = new System.Windows.Forms.RadioButton();
            this.antType1 = new System.Windows.Forms.RadioButton();
            this.gbConnectType = new System.Windows.Forms.GroupBox();
            this.radio_btn_tcp = new System.Windows.Forms.RadioButton();
            this.radio_btn_rs232 = new System.Windows.Forms.RadioButton();
            this.grb_rs232 = new System.Windows.Forms.GroupBox();
            this.btn_refresh_comports = new System.Windows.Forms.Button();
            this.cmbBaudrate = new System.Windows.Forms.ComboBox();
            this.cmbComPort = new System.Windows.Forms.ComboBox();
            this.label2 = new System.Windows.Forms.Label();
            this.label1 = new System.Windows.Forms.Label();
            this.grbModuleBaudRate = new System.Windows.Forms.GroupBox();
            this.btnSetUartBaudrate = new System.Windows.Forms.Button();
            this.cmbSetBaudrate = new System.Windows.Forms.ComboBox();
            this.grb_tcp = new System.Windows.Forms.GroupBox();
            this.txtTcpPort = new System.Windows.Forms.TextBox();
            this.ipIpServer = new IpAddressTextBox();
            this.label4 = new System.Windows.Forms.Label();
            this.label3 = new System.Windows.Forms.Label();
            this.gbCmdReaderAddress = new System.Windows.Forms.GroupBox();
            this.htxtReadId = new HexTextBox();
            this.btnSetReadAddress = new System.Windows.Forms.Button();
            this.gbCmdBaudrate = new System.Windows.Forms.GroupBox();
            this.htbGetIdentifier = new HexTextBox();
            this.htbSetIdentifier = new HexTextBox();
            this.btSetIdentifier = new System.Windows.Forms.Button();
            this.btGetIdentifier = new System.Windows.Forms.Button();
            this.btReaderSetupRefresh = new System.Windows.Forms.Button();
            this.gbCmdReadGpio = new System.Windows.Forms.GroupBox();
            this.groupBox11 = new System.Windows.Forms.GroupBox();
            this.groupBox6 = new System.Windows.Forms.GroupBox();
            this.label33 = new System.Windows.Forms.Label();
            this.rdbGpio3High = new System.Windows.Forms.RadioButton();
            this.rdbGpio3Low = new System.Windows.Forms.RadioButton();
            this.groupBox7 = new System.Windows.Forms.GroupBox();
            this.label32 = new System.Windows.Forms.Label();
            this.rdbGpio4High = new System.Windows.Forms.RadioButton();
            this.rdbGpio4Low = new System.Windows.Forms.RadioButton();
            this.btnWriteGpio4Value = new System.Windows.Forms.Button();
            this.btnWriteGpio3Value = new System.Windows.Forms.Button();
            this.groupBox10 = new System.Windows.Forms.GroupBox();
            this.groupBox4 = new System.Windows.Forms.GroupBox();
            this.label30 = new System.Windows.Forms.Label();
            this.rdbGpio1High = new System.Windows.Forms.RadioButton();
            this.rdbGpio1Low = new System.Windows.Forms.RadioButton();
            this.groupBox5 = new System.Windows.Forms.GroupBox();
            this.label31 = new System.Windows.Forms.Label();
            this.rdbGpio2High = new System.Windows.Forms.RadioButton();
            this.rdbGpio2Low = new System.Windows.Forms.RadioButton();
            this.btnReadGpioValue = new System.Windows.Forms.Button();
            this.gbCmdBeeper = new System.Windows.Forms.GroupBox();
            this.cbbBeepStatus = new System.Windows.Forms.ComboBox();
            this.btnSetBeeperMode = new System.Windows.Forms.Button();
            this.gbCmdTemperature = new System.Windows.Forms.GroupBox();
            this.btnGetReaderTemperature = new System.Windows.Forms.Button();
            this.txtReaderTemperature = new System.Windows.Forms.TextBox();
            this.gbCmdVersion = new System.Windows.Forms.GroupBox();
            this.btnGetFirmwareVersion = new System.Windows.Forms.Button();
            this.txtFirmwareVersion = new System.Windows.Forms.TextBox();
            this.btnResetReader = new System.Windows.Forms.Button();
            this.tabPage2 = new System.Windows.Forms.TabPage();
            this.flowLayoutPanel3 = new System.Windows.Forms.FlowLayoutPanel();
            this.gbCmdRegion = new System.Windows.Forms.GroupBox();
            this.cbUserDefineFreq = new System.Windows.Forms.CheckBox();
            this.groupBox23 = new System.Windows.Forms.GroupBox();
            this.label106 = new System.Windows.Forms.Label();
            this.label105 = new System.Windows.Forms.Label();
            this.label104 = new System.Windows.Forms.Label();
            this.label103 = new System.Windows.Forms.Label();
            this.label86 = new System.Windows.Forms.Label();
            this.label75 = new System.Windows.Forms.Label();
            this.textFreqQuantity = new System.Windows.Forms.TextBox();
            this.TextFreqInterval = new System.Windows.Forms.TextBox();
            this.textStartFreq = new System.Windows.Forms.TextBox();
            this.groupBox21 = new System.Windows.Forms.GroupBox();
            this.label37 = new System.Windows.Forms.Label();
            this.label36 = new System.Windows.Forms.Label();
            this.cmbFrequencyEnd = new System.Windows.Forms.ComboBox();
            this.label13 = new System.Windows.Forms.Label();
            this.cmbFrequencyStart = new System.Windows.Forms.ComboBox();
            this.label12 = new System.Windows.Forms.Label();
            this.rdbRegionChn = new System.Windows.Forms.RadioButton();
            this.rdbRegionEtsi = new System.Windows.Forms.RadioButton();
            this.rdbRegionFcc = new System.Windows.Forms.RadioButton();
            this.btnGetFrequencyRegion = new System.Windows.Forms.Button();
            this.btnSetFrequencyRegion = new System.Windows.Forms.Button();
            this.gbProfile = new System.Windows.Forms.GroupBox();
            this.label19 = new System.Windows.Forms.Label();
            this.cmbModuleLink = new System.Windows.Forms.ComboBox();
            this.btGetProfile = new System.Windows.Forms.Button();
            this.btSetProfile = new System.Windows.Forms.Button();
            this.gbReturnLoss = new System.Windows.Forms.GroupBox();
            this.label110 = new System.Windows.Forms.Label();
            this.label109 = new System.Windows.Forms.Label();
            this.cmbReturnLossFreq = new System.Windows.Forms.ComboBox();
            this.label108 = new System.Windows.Forms.Label();
            this.textReturnLoss = new System.Windows.Forms.TextBox();
            this.btReturnLoss = new System.Windows.Forms.Button();
            this.btRfSetup = new System.Windows.Forms.Button();
            this.gbMonza = new System.Windows.Forms.GroupBox();
            this.label14 = new System.Windows.Forms.Label();
            this.label11 = new System.Windows.Forms.Label();
            this.rdbMonzaOff = new System.Windows.Forms.RadioButton();
            this.btSetMonzaStatus = new System.Windows.Forms.Button();
            this.btGetMonzaStatus = new System.Windows.Forms.Button();
            this.rdbMonzaOn = new System.Windows.Forms.RadioButton();
            this.gbCmdAntDetector = new System.Windows.Forms.GroupBox();
            this.label7 = new System.Windows.Forms.Label();
            this.label6 = new System.Windows.Forms.Label();
            this.label5 = new System.Windows.Forms.Label();
            this.label10 = new System.Windows.Forms.Label();
            this.label8 = new System.Windows.Forms.Label();
            this.tbAntDectector = new System.Windows.Forms.TextBox();
            this.btnGetAntDetector = new System.Windows.Forms.Button();
            this.btnSetAntDetector = new System.Windows.Forms.Button();
            this.gbCmdAntenna = new System.Windows.Forms.GroupBox();
            this.label107 = new System.Windows.Forms.Label();
            this.cmbWorkAnt = new System.Windows.Forms.ComboBox();
            this.btnGetWorkAntenna = new System.Windows.Forms.Button();
            this.btnSetWorkAntenna = new System.Windows.Forms.Button();
            this.gbCmdOutputPower = new System.Windows.Forms.GroupBox();
            this.label151 = new System.Windows.Forms.Label();
            this.label152 = new System.Windows.Forms.Label();
            this.label153 = new System.Windows.Forms.Label();
            this.label154 = new System.Windows.Forms.Label();
            this.tb_outputpower_16 = new System.Windows.Forms.TextBox();
            this.tb_outputpower_15 = new System.Windows.Forms.TextBox();
            this.tb_outputpower_14 = new System.Windows.Forms.TextBox();
            this.tb_outputpower_13 = new System.Windows.Forms.TextBox();
            this.label147 = new System.Windows.Forms.Label();
            this.label148 = new System.Windows.Forms.Label();
            this.label149 = new System.Windows.Forms.Label();
            this.label150 = new System.Windows.Forms.Label();
            this.tb_outputpower_12 = new System.Windows.Forms.TextBox();
            this.tb_outputpower_11 = new System.Windows.Forms.TextBox();
            this.tb_outputpower_10 = new System.Windows.Forms.TextBox();
            this.tb_outputpower_9 = new System.Windows.Forms.TextBox();
            this.label115 = new System.Windows.Forms.Label();
            this.label114 = new System.Windows.Forms.Label();
            this.label113 = new System.Windows.Forms.Label();
            this.label112 = new System.Windows.Forms.Label();
            this.tb_outputpower_8 = new System.Windows.Forms.TextBox();
            this.tb_outputpower_7 = new System.Windows.Forms.TextBox();
            this.tb_outputpower_6 = new System.Windows.Forms.TextBox();
            this.tb_outputpower_5 = new System.Windows.Forms.TextBox();
            this.label34 = new System.Windows.Forms.Label();
            this.label21 = new System.Windows.Forms.Label();
            this.label20 = new System.Windows.Forms.Label();
            this.label18 = new System.Windows.Forms.Label();
            this.tb_outputpower_4 = new System.Windows.Forms.TextBox();
            this.tb_outputpower_3 = new System.Windows.Forms.TextBox();
            this.tb_outputpower_2 = new System.Windows.Forms.TextBox();
            this.tb_outputpower_1 = new System.Windows.Forms.TextBox();
            this.label15 = new System.Windows.Forms.Label();
            this.btnGetOutputPower = new System.Windows.Forms.Button();
            this.btnSetOutputPower = new System.Windows.Forms.Button();
            this.label9 = new System.Windows.Forms.Label();
            this.tabPage4 = new System.Windows.Forms.TabPage();
            this.btE710Refresh = new System.Windows.Forms.Button();
            this.flowLayoutPanel4 = new System.Windows.Forms.FlowLayoutPanel();
            this.gbRfLink = new System.Windows.Forms.GroupBox();
            this.btSetE710Profile = new System.Windows.Forms.Button();
            this.btGetE710Profile = new System.Windows.Forms.Button();
            this.cbbE710RfLink = new System.Windows.Forms.ComboBox();
            this.label40 = new System.Windows.Forms.Label();
            this.cbDrmSwich = new System.Windows.Forms.CheckBox();
            this.grpbQ = new System.Windows.Forms.GroupBox();
            this.btSetQValue = new System.Windows.Forms.Button();
            this.btGetQValue = new System.Windows.Forms.Button();
            this.groupBox34 = new System.Windows.Forms.GroupBox();
            this.tbMaxQSince = new System.Windows.Forms.TextBox();
            this.tbNumMinQ = new System.Windows.Forms.TextBox();
            this.label45 = new System.Windows.Forms.Label();
            this.label44 = new System.Windows.Forms.Label();
            this.cbbMaxQValue = new System.Windows.Forms.ComboBox();
            this.label43 = new System.Windows.Forms.Label();
            this.cbbMinQValue = new System.Windows.Forms.ComboBox();
            this.label42 = new System.Windows.Forms.Label();
            this.cbbInitQValue = new System.Windows.Forms.ComboBox();
            this.label41 = new System.Windows.Forms.Label();
            this.groupBox33 = new System.Windows.Forms.GroupBox();
            this.rbStQ = new System.Windows.Forms.RadioButton();
            this.rbDyQ = new System.Windows.Forms.RadioButton();
            this.groupBox32 = new System.Windows.Forms.GroupBox();
            this.groupBox36 = new System.Windows.Forms.GroupBox();
            this.groupBox38 = new System.Windows.Forms.GroupBox();
            this.label95 = new System.Windows.Forms.Label();
            this.lbModelSendCnt = new System.Windows.Forms.Label();
            this.lbModelTestTimeCnt = new System.Windows.Forms.Label();
            this.label85 = new System.Windows.Forms.Label();
            this.label97 = new System.Windows.Forms.Label();
            this.label74 = new System.Windows.Forms.Label();
            this.lbModelRevCnt = new System.Windows.Forms.Label();
            this.groupBox37 = new System.Windows.Forms.GroupBox();
            this.label94 = new System.Windows.Forms.Label();
            this.lbPCTestTimeCnt = new System.Windows.Forms.Label();
            this.label92 = new System.Windows.Forms.Label();
            this.lbPCRecCnt = new System.Windows.Forms.Label();
            this.label70 = new System.Windows.Forms.Label();
            this.lbPCSendCnt = new System.Windows.Forms.Label();
            this.label60 = new System.Windows.Forms.Label();
            this.groupBox35 = new System.Windows.Forms.GroupBox();
            this.label72 = new System.Windows.Forms.Label();
            this.label62 = new System.Windows.Forms.Label();
            this.tbSendPeroid = new System.Windows.Forms.TextBox();
            this.cbSendPeroid = new System.Windows.Forms.CheckBox();
            this.btnSerialTest = new System.Windows.Forms.Button();
            this.tbTestCmd = new System.Windows.Forms.TextBox();
            this.label52 = new System.Windows.Forms.Label();
            this.tbCmdLen = new System.Windows.Forms.TextBox();
            this.label51 = new System.Windows.Forms.Label();
            this.tbTestCnt = new System.Windows.Forms.TextBox();
            this.label50 = new System.Windows.Forms.Label();
            this.cbbTestModel = new System.Windows.Forms.ComboBox();
            this.label48 = new System.Windows.Forms.Label();
            this.tabPage5 = new System.Windows.Forms.TabPage();
            this.groupBox29 = new System.Windows.Forms.GroupBox();
            this.btSetTm600Profile = new System.Windows.Forms.Button();
            this.btGetTm600Profile = new System.Windows.Forms.Button();
            this.cbbTm600RFLink = new System.Windows.Forms.ComboBox();
            this.label46 = new System.Windows.Forms.Label();
            this.pageEpcTest = new System.Windows.Forms.TabPage();
            this.tab_6c_Tags_Test = new System.Windows.Forms.TabControl();
            this.pageFast4AntMode = new System.Windows.Forms.TabPage();
            this.panel2 = new System.Windows.Forms.Panel();
            this.lLbTagFilter = new System.Windows.Forms.LinkLabel();
            this.flowLayoutPanel1 = new System.Windows.Forms.FlowLayoutPanel();
            this.grb_inventory_cfg = new System.Windows.Forms.GroupBox();
            this.cb_use_selectFlags_tempPows = new System.Windows.Forms.CheckBox();
            this.cb_use_optimize = new System.Windows.Forms.CheckBox();
            this.cb_use_Phase = new System.Windows.Forms.CheckBox();
            this.cb_use_powerSave = new System.Windows.Forms.CheckBox();
            this.cb_customized_session_target = new System.Windows.Forms.CheckBox();
            this.grb_Interval = new System.Windows.Forms.GroupBox();
            this.txtInterval = new System.Windows.Forms.TextBox();
            this.grb_Reserve = new System.Windows.Forms.GroupBox();
            this.tb_fast_inv_reserved_1 = new System.Windows.Forms.TextBox();
            this.tb_fast_inv_reserved_3 = new System.Windows.Forms.TextBox();
            this.tb_fast_inv_reserved_4 = new System.Windows.Forms.TextBox();
            this.tb_fast_inv_reserved_2 = new System.Windows.Forms.TextBox();
            this.tb_fast_inv_reserved_5 = new System.Windows.Forms.TextBox();
            this.grb_selectFlags = new System.Windows.Forms.GroupBox();
            this.radio_btn_sl_03 = new System.Windows.Forms.RadioButton();
            this.radio_btn_sl_02 = new System.Windows.Forms.RadioButton();
            this.radio_btn_sl_01 = new System.Windows.Forms.RadioButton();
            this.radio_btn_sl_00 = new System.Windows.Forms.RadioButton();
            this.grb_sessions = new System.Windows.Forms.GroupBox();
            this.radio_btn_S0 = new System.Windows.Forms.RadioButton();
            this.radio_btn_S1 = new System.Windows.Forms.RadioButton();
            this.radio_btn_S2 = new System.Windows.Forms.RadioButton();
            this.radio_btn_S3 = new System.Windows.Forms.RadioButton();
            this.grb_targets = new System.Windows.Forms.GroupBox();
            this.radio_btn_target_A = new System.Windows.Forms.RadioButton();
            this.radio_btn_target_B = new System.Windows.Forms.RadioButton();
            this.grb_Optimize = new System.Windows.Forms.GroupBox();
            this.txtOptimize = new System.Windows.Forms.TextBox();
            this.grb_Ongoing = new System.Windows.Forms.GroupBox();
            this.txtOngoing = new System.Windows.Forms.TextBox();
            this.grb_TargetQuantity = new System.Windows.Forms.GroupBox();
            this.txtTargetQuantity = new System.Windows.Forms.TextBox();
            this.grb_powerSave = new System.Windows.Forms.GroupBox();
            this.txtPowerSave = new System.Windows.Forms.TextBox();
            this.grb_Repeat = new System.Windows.Forms.GroupBox();
            this.txtRepeat = new System.Windows.Forms.TextBox();
            this.grb_multi_ant = new System.Windows.Forms.GroupBox();
            this.cb_fast_inv_check_all_ant = new System.Windows.Forms.CheckBox();
            this.grb_ants_g1 = new System.Windows.Forms.GroupBox();
            this.chckbx_fast_inv_ant_5 = new System.Windows.Forms.CheckBox();
            this.chckbx_fast_inv_ant_6 = new System.Windows.Forms.CheckBox();
            this.chckbx_fast_inv_ant_1 = new System.Windows.Forms.CheckBox();
            this.txt_fast_inv_Stay_6 = new System.Windows.Forms.TextBox();
            this.chckbx_fast_inv_ant_4 = new System.Windows.Forms.CheckBox();
            this.chckbx_fast_inv_ant_8 = new System.Windows.Forms.CheckBox();
            this.txt_fast_inv_Stay_1 = new System.Windows.Forms.TextBox();
            this.txt_fast_inv_Stay_7 = new System.Windows.Forms.TextBox();
            this.txt_fast_inv_Stay_2 = new System.Windows.Forms.TextBox();
            this.txt_fast_inv_Stay_5 = new System.Windows.Forms.TextBox();
            this.txt_fast_inv_Stay_3 = new System.Windows.Forms.TextBox();
            this.chckbx_fast_inv_ant_7 = new System.Windows.Forms.CheckBox();
            this.chckbx_fast_inv_ant_3 = new System.Windows.Forms.CheckBox();
            this.txt_fast_inv_Stay_8 = new System.Windows.Forms.TextBox();
            this.txt_fast_inv_Stay_4 = new System.Windows.Forms.TextBox();
            this.chckbx_fast_inv_ant_2 = new System.Windows.Forms.CheckBox();
            this.grb_temp_pow_ants_g1 = new System.Windows.Forms.GroupBox();
            this.tv_temp_pow_6 = new System.Windows.Forms.TextBox();
            this.tv_temp_pow_1 = new System.Windows.Forms.TextBox();
            this.tv_temp_pow_5 = new System.Windows.Forms.TextBox();
            this.tv_temp_pow_7 = new System.Windows.Forms.TextBox();
            this.tv_temp_pow_3 = new System.Windows.Forms.TextBox();
            this.tv_temp_pow_8 = new System.Windows.Forms.TextBox();
            this.tv_temp_pow_4 = new System.Windows.Forms.TextBox();
            this.tv_temp_pow_2 = new System.Windows.Forms.TextBox();
            this.grb_ants_g2 = new System.Windows.Forms.GroupBox();
            this.chckbx_fast_inv_ant_9 = new System.Windows.Forms.CheckBox();
            this.chckbx_fast_inv_ant_10 = new System.Windows.Forms.CheckBox();
            this.chckbx_fast_inv_ant_11 = new System.Windows.Forms.CheckBox();
            this.chckbx_fast_inv_ant_12 = new System.Windows.Forms.CheckBox();
            this.chckbx_fast_inv_ant_13 = new System.Windows.Forms.CheckBox();
            this.chckbx_fast_inv_ant_14 = new System.Windows.Forms.CheckBox();
            this.chckbx_fast_inv_ant_15 = new System.Windows.Forms.CheckBox();
            this.chckbx_fast_inv_ant_16 = new System.Windows.Forms.CheckBox();
            this.txt_fast_inv_Stay_9 = new System.Windows.Forms.TextBox();
            this.txt_fast_inv_Stay_10 = new System.Windows.Forms.TextBox();
            this.txt_fast_inv_Stay_11 = new System.Windows.Forms.TextBox();
            this.txt_fast_inv_Stay_12 = new System.Windows.Forms.TextBox();
            this.txt_fast_inv_Stay_13 = new System.Windows.Forms.TextBox();
            this.txt_fast_inv_Stay_14 = new System.Windows.Forms.TextBox();
            this.txt_fast_inv_Stay_16 = new System.Windows.Forms.TextBox();
            this.txt_fast_inv_Stay_15 = new System.Windows.Forms.TextBox();
            this.grb_temp_pow_ants_g2 = new System.Windows.Forms.GroupBox();
            this.tv_temp_pow_16 = new System.Windows.Forms.TextBox();
            this.tv_temp_pow_9 = new System.Windows.Forms.TextBox();
            this.tv_temp_pow_15 = new System.Windows.Forms.TextBox();
            this.tv_temp_pow_10 = new System.Windows.Forms.TextBox();
            this.tv_temp_pow_11 = new System.Windows.Forms.TextBox();
            this.tv_temp_pow_14 = new System.Windows.Forms.TextBox();
            this.tv_temp_pow_12 = new System.Windows.Forms.TextBox();
            this.tv_temp_pow_13 = new System.Windows.Forms.TextBox();
            this.grb_real_inv_ants = new System.Windows.Forms.GroupBox();
            this.label61 = new System.Windows.Forms.Label();
            this.combo_realtime_inv_ants = new System.Windows.Forms.ComboBox();
            this.flowLayoutPanel5 = new System.Windows.Forms.FlowLayoutPanel();
            this.groupBox9 = new System.Windows.Forms.GroupBox();
            this.cmbbxSessionId = new System.Windows.Forms.ComboBox();
            this.bitLen = new System.Windows.Forms.TextBox();
            this.startAddr = new System.Windows.Forms.TextBox();
            this.hexTextBox_mask = new HexTextBox();
            this.label38 = new System.Windows.Forms.Label();
            this.combo_mast_id = new System.Windows.Forms.ComboBox();
            this.label39 = new System.Windows.Forms.Label();
            this.label71 = new System.Windows.Forms.Label();
            this.label99 = new System.Windows.Forms.Label();
            this.label100 = new System.Windows.Forms.Label();
            this.label101 = new System.Windows.Forms.Label();
            this.label102 = new System.Windows.Forms.Label();
            this.combo_menbank = new System.Windows.Forms.ComboBox();
            this.combo_action = new System.Windows.Forms.ComboBox();
            this.btnTagSelect = new System.Windows.Forms.Button();
            this.groupBox12 = new System.Windows.Forms.GroupBox();
            this.label111 = new System.Windows.Forms.Label();
            this.combo_mast_id_Clear = new System.Windows.Forms.ComboBox();
            this.btnClearTagMask = new System.Windows.Forms.Button();
            this.groupBox22 = new System.Windows.Forms.GroupBox();
            this.btnGetTagMask = new System.Windows.Forms.Button();
            this.lLbConfig = new System.Windows.Forms.LinkLabel();
            this.panel14 = new System.Windows.Forms.Panel();
            this.dgvTagMask = new System.Windows.Forms.DataGridView();
            this.tagMask_MaskNoColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.tagMask_SessionIdColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.tagMask_ActionColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.tagMask_MembankColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.tagMask_StartAddrColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.tagMask_MaskLenColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.tagMask_MaskValueColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.tagMask_TruncateColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.groupBox26 = new System.Windows.Forms.GroupBox();
            this.label53 = new System.Windows.Forms.Label();
            this.txtCmdTagCount = new System.Windows.Forms.Label();
            this.label49 = new System.Windows.Forms.Label();
            this.label22 = new System.Windows.Forms.Label();
            this.dgvInventoryTagResults = new System.Windows.Forms.DataGridView();
            this.SerialNumber_fast_inv = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.ReadCount_fast_inv = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.PC_fast_inv = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.EPC_fast_inv = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.Antenna_fast_inv = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.Freq_fast_inv = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.Rssi_fast_inv = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.Phase_fast_inv = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.Data_fast_inv = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.btnFastRefresh = new System.Windows.Forms.Button();
            this.txtFastMinRssi = new System.Windows.Forms.TextBox();
            this.btnSaveTags = new System.Windows.Forms.Button();
            this.txtFastMaxRssi = new System.Windows.Forms.TextBox();
            this.groupBox25 = new System.Windows.Forms.GroupBox();
            this.led_total_tagreads = new Led();
            this.label58 = new System.Windows.Forms.Label();
            this.led_totalread_count = new Led();
            this.led_cmd_readrate = new Led();
            this.label55 = new System.Windows.Forms.Label();
            this.label56 = new System.Windows.Forms.Label();
            this.led_cmd_execute_duration = new Led();
            this.label57 = new System.Windows.Forms.Label();
            this.label54 = new System.Windows.Forms.Label();
            this.ledFast_total_execute_time = new Led();
            this.groupBox2 = new System.Windows.Forms.GroupBox();
            this.grb_inventory_type = new System.Windows.Forms.GroupBox();
            this.rb_fast_inv = new System.Windows.Forms.RadioButton();
            this.radio_btn_fast_inv = new System.Windows.Forms.RadioButton();
            this.radio_btn_realtime_inv = new System.Windows.Forms.RadioButton();
            this.btnInventory = new System.Windows.Forms.Button();
            this.groupBox27 = new System.Windows.Forms.GroupBox();
            this.cb_InvTime = new System.Windows.Forms.CheckBox();
            this.label47 = new System.Windows.Forms.Label();
            this.tb_InvCntTime = new System.Windows.Forms.TextBox();
            this.cb_IceBoxTest = new System.Windows.Forms.CheckBox();
            this.label69 = new System.Windows.Forms.Label();
            this.chkbxSaveLog = new System.Windows.Forms.CheckBox();
            this.chkbxReadBuffer = new System.Windows.Forms.CheckBox();
            this.cb_tagFocus = new System.Windows.Forms.CheckBox();
            this.tb_fast_inv_staytargetB_times = new System.Windows.Forms.TextBox();
            this.lblInvExecTime = new System.Windows.Forms.Label();
            this.mFastIntervalTime = new System.Windows.Forms.TextBox();
            this.lblInvCmdInterval = new System.Windows.Forms.Label();
            this.mInventoryExeCount = new System.Windows.Forms.TextBox();
            this.cb_fast_inv_reverse_target = new System.Windows.Forms.CheckBox();
            this.pageAcessTag = new System.Windows.Forms.TabPage();
            this.gbCmdOperateTag = new System.Windows.Forms.GroupBox();
            this.cbMulAnt = new System.Windows.Forms.CheckBox();
            this.groupBox14 = new System.Windows.Forms.GroupBox();
            this.btnSetTagOpWorkAnt = new System.Windows.Forms.Button();
            this.btnGetTagOpWorkAnt = new System.Windows.Forms.Button();
            this.cmbbxTagOpWorkAnt = new System.Windows.Forms.ComboBox();
            this.chkbxReadTagMultiBankEn = new System.Windows.Forms.CheckBox();
            this.btnStartReadSensorTag = new System.Windows.Forms.Button();
            this.chkbxReadSensorTag = new System.Windows.Forms.CheckBox();
            this.grbSensorType = new System.Windows.Forms.GroupBox();
            this.radio_btn_johar_1 = new System.Windows.Forms.RadioButton();
            this.btnClearTagOpResult = new System.Windows.Forms.Button();
            this.btnReadTag = new System.Windows.Forms.Button();
            this.groupBox28 = new System.Windows.Forms.GroupBox();
            this.label24 = new System.Windows.Forms.Label();
            this.radio_btnBlockWrite = new System.Windows.Forms.RadioButton();
            this.hexTb_WriteData = new HexTextBox();
            this.btnWriteTag = new System.Windows.Forms.Button();
            this.radio_btnWrite = new System.Windows.Forms.RadioButton();
            this.grbReadTagMultiBank = new System.Windows.Forms.GroupBox();
            this.cmbbxReadTagReadMode = new System.Windows.Forms.ComboBox();
            this.cmbbxReadTagTarget = new System.Windows.Forms.ComboBox();
            this.cmbbxReadTagSession = new System.Windows.Forms.ComboBox();
            this.label68 = new System.Windows.Forms.Label();
            this.label67 = new System.Windows.Forms.Label();
            this.label66 = new System.Windows.Forms.Label();
            this.txtbxReadTagUserCnt = new System.Windows.Forms.TextBox();
            this.label64 = new System.Windows.Forms.Label();
            this.txtbxReadTagUserAddr = new System.Windows.Forms.TextBox();
            this.label65 = new System.Windows.Forms.Label();
            this.txtbxReadTagTidCnt = new System.Windows.Forms.TextBox();
            this.label59 = new System.Windows.Forms.Label();
            this.txtbxReadTagTidAddr = new System.Windows.Forms.TextBox();
            this.label63 = new System.Windows.Forms.Label();
            this.txtbxReadTagResCnt = new System.Windows.Forms.TextBox();
            this.label28 = new System.Windows.Forms.Label();
            this.txtbxReadTagResAddr = new System.Windows.Forms.TextBox();
            this.label25 = new System.Windows.Forms.Label();
            this.dgvTagOp = new System.Windows.Forms.DataGridView();
            this.tagOp_SerialNumberColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.tagOp_PcColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.tagOp_CrcColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.tagOp_EpcColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.tagOp_DataColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.tagOp_DataLenColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.tagOp_AntennaColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.tagOp_OpCountColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.tagOp_FreqColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.tagOp_TemperatureColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.groupBox3 = new System.Windows.Forms.GroupBox();
            this.hexTb_accessPw = new HexTextBox();
            this.groupBox31 = new System.Windows.Forms.GroupBox();
            this.rdbUser = new System.Windows.Forms.RadioButton();
            this.label26 = new System.Windows.Forms.Label();
            this.tb_startWord = new System.Windows.Forms.TextBox();
            this.rdbTid = new System.Windows.Forms.RadioButton();
            this.label27 = new System.Windows.Forms.Label();
            this.tb_wordLen = new System.Windows.Forms.TextBox();
            this.rdbEpc = new System.Windows.Forms.RadioButton();
            this.rdbReserved = new System.Windows.Forms.RadioButton();
            this.groupBox16 = new System.Windows.Forms.GroupBox();
            this.btnKillTag = new System.Windows.Forms.Button();
            this.htxtKillPwd = new HexTextBox();
            this.label29 = new System.Windows.Forms.Label();
            this.groupBox15 = new System.Windows.Forms.GroupBox();
            this.groupBox19 = new System.Windows.Forms.GroupBox();
            this.rdbUserMemory = new System.Windows.Forms.RadioButton();
            this.rdbTidMemory = new System.Windows.Forms.RadioButton();
            this.rdbEpcMermory = new System.Windows.Forms.RadioButton();
            this.rdbKillPwd = new System.Windows.Forms.RadioButton();
            this.rdbAccessPwd = new System.Windows.Forms.RadioButton();
            this.groupBox18 = new System.Windows.Forms.GroupBox();
            this.rdbLockEver = new System.Windows.Forms.RadioButton();
            this.rdbFreeEver = new System.Windows.Forms.RadioButton();
            this.rdbLock = new System.Windows.Forms.RadioButton();
            this.rdbFree = new System.Windows.Forms.RadioButton();
            this.btnLockTag = new System.Windows.Forms.Button();
            this.groupBox13 = new System.Windows.Forms.GroupBox();
            this.btnCancelAccessEpcMatch = new System.Windows.Forms.Button();
            this.btnGetAccessEpcMatch = new System.Windows.Forms.Button();
            this.label23 = new System.Windows.Forms.Label();
            this.btnSetAccessEpcMatch = new System.Windows.Forms.Button();
            this.cmbSetAccessEpcMatch = new System.Windows.Forms.ComboBox();
            this.txtAccessEpcMatch = new System.Windows.Forms.TextBox();
            this.PagTranDataLog = new System.Windows.Forms.TabPage();
            this.lrtxtDataTran = new LogRichTextBox();
            this.panel3 = new System.Windows.Forms.Panel();
            this.label16 = new System.Windows.Forms.Label();
            this.htxtSendData = new HexTextBox();
            this.btnSaveData = new System.Windows.Forms.Button();
            this.btnClearData = new System.Windows.Forms.Button();
            this.htxtCheckData = new HexTextBox();
            this.label17 = new System.Windows.Forms.Label();
            this.btnSendData = new System.Windows.Forms.Button();
            this.net_configure_tabPage = new System.Windows.Forms.TabPage();
            this.groupBox20 = new System.Windows.Forms.GroupBox();
            this.btnGetNetport = new System.Windows.Forms.Button();
            this.btnSetNetport = new System.Windows.Forms.Button();
            this.net_load_cfg_btn = new System.Windows.Forms.Button();
            this.btnResetNetport = new System.Windows.Forms.Button();
            this.net_save_cfg_btn = new System.Windows.Forms.Button();
            this.btnDefaultNetPort = new System.Windows.Forms.Button();
            this.groupBox17 = new System.Windows.Forms.GroupBox();
            this.linklblOldNetPortCfgTool_Link = new System.Windows.Forms.LinkLabel();
            this.label164 = new System.Windows.Forms.Label();
            this.label165 = new System.Windows.Forms.Label();
            this.linklblNetPortCfgTool_Link = new System.Windows.Forms.LinkLabel();
            this.lblNetPortCount = new System.Windows.Forms.Label();
            this.port_setting_tabcontrol = new System.Windows.Forms.TabControl();
            this.net_port_0_tabPage = new System.Windows.Forms.TabPage();
            this.grbDnsDomain = new System.Windows.Forms.GroupBox();
            this.txtbxPort1_DnsDomain = new System.Windows.Forms.TextBox();
            this.grbDesIpPort = new System.Windows.Forms.GroupBox();
            this.txtbxPort1_DesIp = new System.Windows.Forms.TextBox();
            this.txtbxPort1_DesPort = new System.Windows.Forms.TextBox();
            this.label203 = new System.Windows.Forms.Label();
            this.txtbxPort1_Dnsport = new System.Windows.Forms.TextBox();
            this.label202 = new System.Windows.Forms.Label();
            this.txtbxPort1_DnsIp = new System.Windows.Forms.TextBox();
            this.label128 = new System.Windows.Forms.Label();
            this.txtbxPort1_ReConnectCnt = new System.Windows.Forms.TextBox();
            this.chkbxPort1_DomainEn = new System.Windows.Forms.CheckBox();
            this.label192 = new System.Windows.Forms.Label();
            this.label190 = new System.Windows.Forms.Label();
            this.label191 = new System.Windows.Forms.Label();
            this.chkbxPort1_ResetCtrl = new System.Windows.Forms.CheckBox();
            this.label189 = new System.Windows.Forms.Label();
            this.txtbxPort1_RxTimeout = new System.Windows.Forms.TextBox();
            this.label188 = new System.Windows.Forms.Label();
            this.txtbxPort1_RxPkgLen = new System.Windows.Forms.TextBox();
            this.label180 = new System.Windows.Forms.Label();
            this.chkbxPort1_PhyDisconnect = new System.Windows.Forms.CheckBox();
            this.chkbxPort1_PortEn = new System.Windows.Forms.CheckBox();
            this.chkbxPort1_RandEn = new System.Windows.Forms.CheckBox();
            this.label169 = new System.Windows.Forms.Label();
            this.cmbbxPort1_Parity = new System.Windows.Forms.ComboBox();
            this.label168 = new System.Windows.Forms.Label();
            this.cmbbxPort1_StopBits = new System.Windows.Forms.ComboBox();
            this.label167 = new System.Windows.Forms.Label();
            this.cmbbxPort1_DataSize = new System.Windows.Forms.ComboBox();
            this.label166 = new System.Windows.Forms.Label();
            this.cmbbxPort1_BaudRate = new System.Windows.Forms.ComboBox();
            this.txtbxPort1_NetPort = new System.Windows.Forms.TextBox();
            this.label126 = new System.Windows.Forms.Label();
            this.label125 = new System.Windows.Forms.Label();
            this.cmbbxPort1_NetMode = new System.Windows.Forms.ComboBox();
            this.net_port_1_tabPage = new System.Windows.Forms.TabPage();
            this.grbHeartbeat = new System.Windows.Forms.GroupBox();
            this.label175 = new System.Windows.Forms.Label();
            this.txtbxHeartbeatContent = new System.Windows.Forms.TextBox();
            this.txtbxHeartbeatInterval = new System.Windows.Forms.TextBox();
            this.label174 = new System.Windows.Forms.Label();
            this.chkbxPort0PortEn = new System.Windows.Forms.CheckBox();
            this.btnClearNetPort = new System.Windows.Forms.Button();
            this.net_base_settings_gb = new System.Windows.Forms.GroupBox();
            this.txtbxHwCfgMac = new System.Windows.Forms.TextBox();
            this.label157 = new System.Windows.Forms.Label();
            this.label193 = new System.Windows.Forms.Label();
            this.chkbxHwCfgComCfgEn = new System.Windows.Forms.CheckBox();
            this.chkbxHwCfgDhcpEn = new System.Windows.Forms.CheckBox();
            this.txtbxHwCfgGateway = new System.Windows.Forms.TextBox();
            this.txtbxHwCfgMask = new System.Windows.Forms.TextBox();
            this.txtbxHwCfgIp = new System.Windows.Forms.TextBox();
            this.txtbxHwCfgDeviceName = new System.Windows.Forms.TextBox();
            this.label161 = new System.Windows.Forms.Label();
            this.label160 = new System.Windows.Forms.Label();
            this.label158 = new System.Windows.Forms.Label();
            this.label156 = new System.Windows.Forms.Label();
            this.dgvNetPort = new System.Windows.Forms.DataGridView();
            this.npSerialNumberColumn = new System.Windows.Forms.DataGridViewCheckBoxColumn();
            this.npDeviceNameColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.npDeviceIpColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.npDeviceMacColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.npChipVerColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.npPcMacColumn = new System.Windows.Forms.DataGridViewTextBoxColumn();
            this.label159 = new System.Windows.Forms.Label();
            this.cmbbxNetCard = new System.Windows.Forms.ComboBox();
            this.groupBox30 = new System.Windows.Forms.GroupBox();
            this.lblCurPcMac = new System.Windows.Forms.Label();
            this.lblCurNetcard = new System.Windows.Forms.Label();
            this.btnSearchNetport = new System.Windows.Forms.Button();
            this.net_refresh_netcard_btn = new System.Windows.Forms.Button();
            this.PagSpecialFeature = new System.Windows.Forms.TabPage();
            this.btn_RefreshSpecial = new System.Windows.Forms.Button();
            this.groupBox39 = new System.Windows.Forms.GroupBox();
            this.linkLabel1 = new System.Windows.Forms.LinkLabel();
            this.label73 = new System.Windows.Forms.Label();
            this.groupBox40 = new System.Windows.Forms.GroupBox();
            this.label121 = new System.Windows.Forms.Label();
            this.label122 = new System.Windows.Forms.Label();
            this.txtHStay = new System.Windows.Forms.TextBox();
            this.cmbAntSelect8 = new System.Windows.Forms.ComboBox();
            this.label123 = new System.Windows.Forms.Label();
            this.label124 = new System.Windows.Forms.Label();
            this.txtGStay = new System.Windows.Forms.TextBox();
            this.cmbAntSelect7 = new System.Windows.Forms.ComboBox();
            this.label127 = new System.Windows.Forms.Label();
            this.label129 = new System.Windows.Forms.Label();
            this.txtFStay = new System.Windows.Forms.TextBox();
            this.cmbAntSelect6 = new System.Windows.Forms.ComboBox();
            this.label130 = new System.Windows.Forms.Label();
            this.label131 = new System.Windows.Forms.Label();
            this.txtEStay = new System.Windows.Forms.TextBox();
            this.cmbAntSelect5 = new System.Windows.Forms.ComboBox();
            this.tb_Interval = new System.Windows.Forms.TextBox();
            this.label84 = new System.Windows.Forms.Label();
            this.btn_GetAntSwitch = new System.Windows.Forms.Button();
            this.btn_SetAntSwitch = new System.Windows.Forms.Button();
            this.label93 = new System.Windows.Forms.Label();
            this.label96 = new System.Windows.Forms.Label();
            this.txtDStay = new System.Windows.Forms.TextBox();
            this.cmbAntSelect4 = new System.Windows.Forms.ComboBox();
            this.label98 = new System.Windows.Forms.Label();
            this.label116 = new System.Windows.Forms.Label();
            this.txtCStay = new System.Windows.Forms.TextBox();
            this.cmbAntSelect3 = new System.Windows.Forms.ComboBox();
            this.label117 = new System.Windows.Forms.Label();
            this.label118 = new System.Windows.Forms.Label();
            this.txtBStay = new System.Windows.Forms.TextBox();
            this.cmbAntSelect2 = new System.Windows.Forms.ComboBox();
            this.label119 = new System.Windows.Forms.Label();
            this.label120 = new System.Windows.Forms.Label();
            this.txtAStay = new System.Windows.Forms.TextBox();
            this.cmbAntSelect1 = new System.Windows.Forms.ComboBox();
            this.cbb_FunctionId = new System.Windows.Forms.ComboBox();
            this.btn_SetFunction = new System.Windows.Forms.Button();
            this.btn_GetFunction = new System.Windows.Forms.Button();
            this.label35 = new System.Windows.Forms.Label();
            this.ckDisplayLog = new System.Windows.Forms.CheckBox();
            this.tableLayoutPanel3 = new System.Windows.Forms.TableLayoutPanel();
            this.panel6 = new System.Windows.Forms.Panel();
            this.button4 = new System.Windows.Forms.Button();
            this.panel7 = new System.Windows.Forms.Panel();
            this.checkBox5 = new System.Windows.Forms.CheckBox();
            this.checkBox6 = new System.Windows.Forms.CheckBox();
            this.checkBox7 = new System.Windows.Forms.CheckBox();
            this.checkBox8 = new System.Windows.Forms.CheckBox();
            this.textBox5 = new System.Windows.Forms.TextBox();
            this.textBox6 = new System.Windows.Forms.TextBox();
            this.button5 = new System.Windows.Forms.Button();
            this.label76 = new System.Windows.Forms.Label();
            this.label77 = new System.Windows.Forms.Label();
            this.label78 = new System.Windows.Forms.Label();
            this.groupBox8 = new System.Windows.Forms.GroupBox();
            this.comboBox9 = new System.Windows.Forms.ComboBox();
            this.ledControl9 = new Led();
            this.ledControl10 = new Led();
            this.ledControl11 = new Led();
            this.ledControl12 = new Led();
            this.label79 = new System.Windows.Forms.Label();
            this.label80 = new System.Windows.Forms.Label();
            this.label81 = new System.Windows.Forms.Label();
            this.label82 = new System.Windows.Forms.Label();
            this.label83 = new System.Windows.Forms.Label();
            this.ledControl13 = new Led();
            this.listView1 = new System.Windows.Forms.ListView();
            this.columnHeader43 = ((System.Windows.Forms.ColumnHeader)(new System.Windows.Forms.ColumnHeader()));
            this.columnHeader44 = ((System.Windows.Forms.ColumnHeader)(new System.Windows.Forms.ColumnHeader()));
            this.columnHeader45 = ((System.Windows.Forms.ColumnHeader)(new System.Windows.Forms.ColumnHeader()));
            this.columnHeader46 = ((System.Windows.Forms.ColumnHeader)(new System.Windows.Forms.ColumnHeader()));
            this.columnHeader47 = ((System.Windows.Forms.ColumnHeader)(new System.Windows.Forms.ColumnHeader()));
            this.columnHeader48 = ((System.Windows.Forms.ColumnHeader)(new System.Windows.Forms.ColumnHeader()));
            this.comboBox10 = new System.Windows.Forms.ComboBox();
            this.label87 = new System.Windows.Forms.Label();
            this.label88 = new System.Windows.Forms.Label();
            this.label89 = new System.Windows.Forms.Label();
            this.label90 = new System.Windows.Forms.Label();
            this.label91 = new System.Windows.Forms.Label();
            this.ckClearOperationRec = new System.Windows.Forms.CheckBox();
            this.panel1 = new System.Windows.Forms.Panel();
            this.lrtxtLog = new LogRichTextBox();
            this.ledControl14 = new Led();
            this.ledControl15 = new Led();
            this.ledControl16 = new Led();
            this.ledControl17 = new Led();
            this.ledControl18 = new Led();
            this.tabCtrMain.SuspendLayout();
            this.PagReaderSetting.SuspendLayout();
            this.tabControl_baseSettings.SuspendLayout();
            this.tabPage1.SuspendLayout();
            this.flowLayoutPanel2.SuspendLayout();
            this.gbModel.SuspendLayout();
            this.groupBox1.SuspendLayout();
            this.groupBox24.SuspendLayout();
            this.gbConnectType.SuspendLayout();
            this.grb_rs232.SuspendLayout();
            this.grbModuleBaudRate.SuspendLayout();
            this.grb_tcp.SuspendLayout();
            this.gbCmdReaderAddress.SuspendLayout();
            this.gbCmdBaudrate.SuspendLayout();
            this.gbCmdReadGpio.SuspendLayout();
            this.groupBox11.SuspendLayout();
            this.groupBox6.SuspendLayout();
            this.groupBox7.SuspendLayout();
            this.groupBox10.SuspendLayout();
            this.groupBox4.SuspendLayout();
            this.groupBox5.SuspendLayout();
            this.gbCmdBeeper.SuspendLayout();
            this.gbCmdTemperature.SuspendLayout();
            this.gbCmdVersion.SuspendLayout();
            this.tabPage2.SuspendLayout();
            this.flowLayoutPanel3.SuspendLayout();
            this.gbCmdRegion.SuspendLayout();
            this.groupBox23.SuspendLayout();
            this.groupBox21.SuspendLayout();
            this.gbProfile.SuspendLayout();
            this.gbReturnLoss.SuspendLayout();
            this.gbMonza.SuspendLayout();
            this.gbCmdAntDetector.SuspendLayout();
            this.gbCmdAntenna.SuspendLayout();
            this.gbCmdOutputPower.SuspendLayout();
            this.tabPage4.SuspendLayout();
            this.flowLayoutPanel4.SuspendLayout();
            this.gbRfLink.SuspendLayout();
            this.grpbQ.SuspendLayout();
            this.groupBox34.SuspendLayout();
            this.groupBox33.SuspendLayout();
            this.groupBox32.SuspendLayout();
            this.groupBox36.SuspendLayout();
            this.groupBox38.SuspendLayout();
            this.groupBox37.SuspendLayout();
            this.groupBox35.SuspendLayout();
            this.tabPage5.SuspendLayout();
            this.groupBox29.SuspendLayout();
            this.pageEpcTest.SuspendLayout();
            this.tab_6c_Tags_Test.SuspendLayout();
            this.pageFast4AntMode.SuspendLayout();
            this.panel2.SuspendLayout();
            this.flowLayoutPanel1.SuspendLayout();
            this.grb_inventory_cfg.SuspendLayout();
            this.grb_Interval.SuspendLayout();
            this.grb_Reserve.SuspendLayout();
            this.grb_selectFlags.SuspendLayout();
            this.grb_sessions.SuspendLayout();
            this.grb_targets.SuspendLayout();
            this.grb_Optimize.SuspendLayout();
            this.grb_Ongoing.SuspendLayout();
            this.grb_TargetQuantity.SuspendLayout();
            this.grb_powerSave.SuspendLayout();
            this.grb_Repeat.SuspendLayout();
            this.grb_multi_ant.SuspendLayout();
            this.grb_ants_g1.SuspendLayout();
            this.grb_temp_pow_ants_g1.SuspendLayout();
            this.grb_ants_g2.SuspendLayout();
            this.grb_temp_pow_ants_g2.SuspendLayout();
            this.grb_real_inv_ants.SuspendLayout();
            this.flowLayoutPanel5.SuspendLayout();
            this.groupBox9.SuspendLayout();
            this.groupBox12.SuspendLayout();
            this.groupBox22.SuspendLayout();
            this.panel14.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.dgvTagMask)).BeginInit();
            this.groupBox26.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.dgvInventoryTagResults)).BeginInit();
            this.groupBox25.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.led_total_tagreads)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.led_totalread_count)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.led_cmd_readrate)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.led_cmd_execute_duration)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.ledFast_total_execute_time)).BeginInit();
            this.groupBox2.SuspendLayout();
            this.grb_inventory_type.SuspendLayout();
            this.groupBox27.SuspendLayout();
            this.pageAcessTag.SuspendLayout();
            this.gbCmdOperateTag.SuspendLayout();
            this.groupBox14.SuspendLayout();
            this.grbSensorType.SuspendLayout();
            this.groupBox28.SuspendLayout();
            this.grbReadTagMultiBank.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.dgvTagOp)).BeginInit();
            this.groupBox3.SuspendLayout();
            this.groupBox31.SuspendLayout();
            this.groupBox16.SuspendLayout();
            this.groupBox15.SuspendLayout();
            this.groupBox19.SuspendLayout();
            this.groupBox18.SuspendLayout();
            this.groupBox13.SuspendLayout();
            this.PagTranDataLog.SuspendLayout();
            this.panel3.SuspendLayout();
            this.net_configure_tabPage.SuspendLayout();
            this.groupBox20.SuspendLayout();
            this.groupBox17.SuspendLayout();
            this.port_setting_tabcontrol.SuspendLayout();
            this.net_port_0_tabPage.SuspendLayout();
            this.grbDnsDomain.SuspendLayout();
            this.grbDesIpPort.SuspendLayout();
            this.net_port_1_tabPage.SuspendLayout();
            this.grbHeartbeat.SuspendLayout();
            this.net_base_settings_gb.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.dgvNetPort)).BeginInit();
            this.groupBox30.SuspendLayout();
            this.PagSpecialFeature.SuspendLayout();
            this.groupBox39.SuspendLayout();
            this.groupBox40.SuspendLayout();
            this.tableLayoutPanel3.SuspendLayout();
            this.panel6.SuspendLayout();
            this.panel7.SuspendLayout();
            this.groupBox8.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.ledControl9)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.ledControl10)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.ledControl11)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.ledControl12)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.ledControl13)).BeginInit();
            this.panel1.SuspendLayout();
            ((System.ComponentModel.ISupportInitialize)(this.ledControl14)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.ledControl15)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.ledControl16)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.ledControl17)).BeginInit();
            ((System.ComponentModel.ISupportInitialize)(this.ledControl18)).BeginInit();
            this.SuspendLayout();
            // 
            // tabCtrMain
            // 
            resources.ApplyResources(this.tabCtrMain, "tabCtrMain");
            this.tabCtrMain.Controls.Add(this.PagReaderSetting);
            this.tabCtrMain.Controls.Add(this.pageEpcTest);
            this.tabCtrMain.Controls.Add(this.PagTranDataLog);
            this.tabCtrMain.Controls.Add(this.net_configure_tabPage);
            this.tabCtrMain.Controls.Add(this.PagSpecialFeature);
            this.tabCtrMain.Name = "tabCtrMain";
            this.tabCtrMain.SelectedIndex = 0;
            this.tabCtrMain.SelectedIndexChanged += new System.EventHandler(this.tabCtrMain_SelectedIndexChanged);
            // 
            // PagReaderSetting
            // 
            resources.ApplyResources(this.PagReaderSetting, "PagReaderSetting");
            this.PagReaderSetting.BackColor = System.Drawing.Color.WhiteSmoke;
            this.PagReaderSetting.Controls.Add(this.tabControl_baseSettings);
            this.PagReaderSetting.Name = "PagReaderSetting";
            // 
            // tabControl_baseSettings
            // 
            resources.ApplyResources(this.tabControl_baseSettings, "tabControl_baseSettings");
            this.tabControl_baseSettings.Controls.Add(this.tabPage1);
            this.tabControl_baseSettings.Controls.Add(this.tabPage2);
            this.tabControl_baseSettings.Controls.Add(this.tabPage4);
            this.tabControl_baseSettings.Controls.Add(this.tabPage5);
            this.tabControl_baseSettings.Name = "tabControl_baseSettings";
            this.tabControl_baseSettings.SelectedIndex = 0;
            // 
            // tabPage1
            // 
            resources.ApplyResources(this.tabPage1, "tabPage1");
            this.tabPage1.BackColor = System.Drawing.Color.WhiteSmoke;
            this.tabPage1.Controls.Add(this.btnFactoryReset);
            this.tabPage1.Controls.Add(this.flowLayoutPanel2);
            this.tabPage1.Controls.Add(this.btReaderSetupRefresh);
            this.tabPage1.Controls.Add(this.gbCmdReadGpio);
            this.tabPage1.Controls.Add(this.gbCmdBeeper);
            this.tabPage1.Controls.Add(this.gbCmdTemperature);
            this.tabPage1.Controls.Add(this.gbCmdVersion);
            this.tabPage1.Controls.Add(this.btnResetReader);
            this.tabPage1.Name = "tabPage1";
            // 
            // btnFactoryReset
            // 
            resources.ApplyResources(this.btnFactoryReset, "btnFactoryReset");
            this.btnFactoryReset.Name = "btnFactoryReset";
            this.btnFactoryReset.UseVisualStyleBackColor = true;
            this.btnFactoryReset.Click += new System.EventHandler(this.btnFactoryReset_Click);
            // 
            // flowLayoutPanel2
            // 
            resources.ApplyResources(this.flowLayoutPanel2, "flowLayoutPanel2");
            this.flowLayoutPanel2.Controls.Add(this.gbModel);
            this.flowLayoutPanel2.Controls.Add(this.groupBox1);
            this.flowLayoutPanel2.Controls.Add(this.grb_rs232);
            this.flowLayoutPanel2.Controls.Add(this.grbModuleBaudRate);
            this.flowLayoutPanel2.Controls.Add(this.grb_tcp);
            this.flowLayoutPanel2.Controls.Add(this.gbCmdReaderAddress);
            this.flowLayoutPanel2.Controls.Add(this.gbCmdBaudrate);
            this.flowLayoutPanel2.Name = "flowLayoutPanel2";
            // 
            // gbModel
            // 
            resources.ApplyResources(this.gbModel, "gbModel");
            this.gbModel.Controls.Add(this.rb_E710);
            this.gbModel.Controls.Add(this.rb_R2000);
            this.gbModel.Name = "gbModel";
            this.gbModel.TabStop = false;
            // 
            // rb_E710
            // 
            resources.ApplyResources(this.rb_E710, "rb_E710");
            this.rb_E710.Name = "rb_E710";
            this.rb_E710.TabStop = true;
            this.rb_E710.UseVisualStyleBackColor = true;
            this.rb_E710.CheckedChanged += new System.EventHandler(this.ModelE710_CheckedChanged);
            // 
            // rb_R2000
            // 
            resources.ApplyResources(this.rb_R2000, "rb_R2000");
            this.rb_R2000.Name = "rb_R2000";
            this.rb_R2000.TabStop = true;
            this.rb_R2000.UseVisualStyleBackColor = true;
            this.rb_R2000.CheckedChanged += new System.EventHandler(this.ModelR2000_CheckedChanged);
            // 
            // groupBox1
            // 
            resources.ApplyResources(this.groupBox1, "groupBox1");
            this.groupBox1.Controls.Add(this.btnConnect);
            this.groupBox1.Controls.Add(this.groupBox24);
            this.groupBox1.Controls.Add(this.gbConnectType);
            this.groupBox1.Name = "groupBox1";
            this.groupBox1.TabStop = false;
            // 
            // btnConnect
            // 
            resources.ApplyResources(this.btnConnect, "btnConnect");
            this.btnConnect.Name = "btnConnect";
            this.btnConnect.UseVisualStyleBackColor = true;
            this.btnConnect.Click += new System.EventHandler(this.btnConnect_Click);
            // 
            // groupBox24
            // 
            resources.ApplyResources(this.groupBox24, "groupBox24");
            this.groupBox24.Controls.Add(this.antType16);
            this.groupBox24.Controls.Add(this.antType8);
            this.groupBox24.Controls.Add(this.antType4);
            this.groupBox24.Controls.Add(this.antType1);
            this.groupBox24.Name = "groupBox24";
            this.groupBox24.TabStop = false;
            // 
            // antType16
            // 
            resources.ApplyResources(this.antType16, "antType16");
            this.antType16.Name = "antType16";
            this.antType16.TabStop = true;
            this.antType16.UseVisualStyleBackColor = true;
            this.antType16.CheckedChanged += new System.EventHandler(this.antType_CheckedChanged);
            // 
            // antType8
            // 
            resources.ApplyResources(this.antType8, "antType8");
            this.antType8.Name = "antType8";
            this.antType8.TabStop = true;
            this.antType8.UseVisualStyleBackColor = true;
            this.antType8.CheckedChanged += new System.EventHandler(this.antType_CheckedChanged);
            // 
            // antType4
            // 
            resources.ApplyResources(this.antType4, "antType4");
            this.antType4.Name = "antType4";
            this.antType4.TabStop = true;
            this.antType4.UseVisualStyleBackColor = true;
            this.antType4.CheckedChanged += new System.EventHandler(this.antType_CheckedChanged);
            // 
            // antType1
            // 
            resources.ApplyResources(this.antType1, "antType1");
            this.antType1.Name = "antType1";
            this.antType1.TabStop = true;
            this.antType1.UseVisualStyleBackColor = true;
            this.antType1.CheckedChanged += new System.EventHandler(this.antType_CheckedChanged);
            // 
            // gbConnectType
            // 
            resources.ApplyResources(this.gbConnectType, "gbConnectType");
            this.gbConnectType.Controls.Add(this.radio_btn_tcp);
            this.gbConnectType.Controls.Add(this.radio_btn_rs232);
            this.gbConnectType.Name = "gbConnectType";
            this.gbConnectType.TabStop = false;
            // 
            // radio_btn_tcp
            // 
            resources.ApplyResources(this.radio_btn_tcp, "radio_btn_tcp");
            this.radio_btn_tcp.Name = "radio_btn_tcp";
            this.radio_btn_tcp.TabStop = true;
            this.radio_btn_tcp.UseVisualStyleBackColor = true;
            this.radio_btn_tcp.CheckedChanged += new System.EventHandler(this.connectType_CheckedChanged);
            // 
            // radio_btn_rs232
            // 
            resources.ApplyResources(this.radio_btn_rs232, "radio_btn_rs232");
            this.radio_btn_rs232.Name = "radio_btn_rs232";
            this.radio_btn_rs232.TabStop = true;
            this.radio_btn_rs232.UseVisualStyleBackColor = true;
            this.radio_btn_rs232.CheckedChanged += new System.EventHandler(this.connectType_CheckedChanged);
            // 
            // grb_rs232
            // 
            resources.ApplyResources(this.grb_rs232, "grb_rs232");
            this.grb_rs232.Controls.Add(this.btn_refresh_comports);
            this.grb_rs232.Controls.Add(this.cmbBaudrate);
            this.grb_rs232.Controls.Add(this.cmbComPort);
            this.grb_rs232.Controls.Add(this.label2);
            this.grb_rs232.Controls.Add(this.label1);
            this.grb_rs232.Name = "grb_rs232";
            this.grb_rs232.TabStop = false;
            // 
            // btn_refresh_comports
            // 
            resources.ApplyResources(this.btn_refresh_comports, "btn_refresh_comports");
            this.btn_refresh_comports.Name = "btn_refresh_comports";
            this.btn_refresh_comports.UseVisualStyleBackColor = true;
            this.btn_refresh_comports.Click += new System.EventHandler(this.btn_refresh_comports_Click);
            // 
            // cmbBaudrate
            // 
            resources.ApplyResources(this.cmbBaudrate, "cmbBaudrate");
            this.cmbBaudrate.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbBaudrate.FormattingEnabled = true;
            this.cmbBaudrate.Name = "cmbBaudrate";
            // 
            // cmbComPort
            // 
            resources.ApplyResources(this.cmbComPort, "cmbComPort");
            this.cmbComPort.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbComPort.FormattingEnabled = true;
            this.cmbComPort.Name = "cmbComPort";
            // 
            // label2
            // 
            resources.ApplyResources(this.label2, "label2");
            this.label2.Name = "label2";
            // 
            // label1
            // 
            resources.ApplyResources(this.label1, "label1");
            this.label1.Name = "label1";
            // 
            // grbModuleBaudRate
            // 
            resources.ApplyResources(this.grbModuleBaudRate, "grbModuleBaudRate");
            this.grbModuleBaudRate.Controls.Add(this.btnSetUartBaudrate);
            this.grbModuleBaudRate.Controls.Add(this.cmbSetBaudrate);
            this.grbModuleBaudRate.Name = "grbModuleBaudRate";
            this.grbModuleBaudRate.TabStop = false;
            // 
            // btnSetUartBaudrate
            // 
            resources.ApplyResources(this.btnSetUartBaudrate, "btnSetUartBaudrate");
            this.btnSetUartBaudrate.Name = "btnSetUartBaudrate";
            this.btnSetUartBaudrate.UseVisualStyleBackColor = true;
            this.btnSetUartBaudrate.Click += new System.EventHandler(this.btnSetUartBaudrate_Click);
            // 
            // cmbSetBaudrate
            // 
            resources.ApplyResources(this.cmbSetBaudrate, "cmbSetBaudrate");
            this.cmbSetBaudrate.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbSetBaudrate.FormattingEnabled = true;
            this.cmbSetBaudrate.Name = "cmbSetBaudrate";
            // 
            // grb_tcp
            // 
            resources.ApplyResources(this.grb_tcp, "grb_tcp");
            this.grb_tcp.Controls.Add(this.txtTcpPort);
            this.grb_tcp.Controls.Add(this.ipIpServer);
            this.grb_tcp.Controls.Add(this.label4);
            this.grb_tcp.Controls.Add(this.label3);
            this.grb_tcp.Name = "grb_tcp";
            this.grb_tcp.TabStop = false;
            // 
            // txtTcpPort
            // 
            resources.ApplyResources(this.txtTcpPort, "txtTcpPort");
            this.txtTcpPort.Name = "txtTcpPort";
            // 
            // ipIpServer
            // 
            resources.ApplyResources(this.ipIpServer, "ipIpServer");
            this.ipIpServer.IpAddressStr = "";
            this.ipIpServer.Name = "ipIpServer";
            // 
            // label4
            // 
            resources.ApplyResources(this.label4, "label4");
            this.label4.Name = "label4";
            // 
            // label3
            // 
            resources.ApplyResources(this.label3, "label3");
            this.label3.Name = "label3";
            // 
            // gbCmdReaderAddress
            // 
            resources.ApplyResources(this.gbCmdReaderAddress, "gbCmdReaderAddress");
            this.gbCmdReaderAddress.Controls.Add(this.htxtReadId);
            this.gbCmdReaderAddress.Controls.Add(this.btnSetReadAddress);
            this.gbCmdReaderAddress.ForeColor = System.Drawing.Color.Black;
            this.gbCmdReaderAddress.Name = "gbCmdReaderAddress";
            this.gbCmdReaderAddress.TabStop = false;
            // 
            // htxtReadId
            // 
            resources.ApplyResources(this.htxtReadId, "htxtReadId");
            this.htxtReadId.Name = "htxtReadId";
            // 
            // btnSetReadAddress
            // 
            resources.ApplyResources(this.btnSetReadAddress, "btnSetReadAddress");
            this.btnSetReadAddress.Name = "btnSetReadAddress";
            this.btnSetReadAddress.UseVisualStyleBackColor = true;
            this.btnSetReadAddress.Click += new System.EventHandler(this.btnSetReadAddress_Click);
            // 
            // gbCmdBaudrate
            // 
            resources.ApplyResources(this.gbCmdBaudrate, "gbCmdBaudrate");
            this.gbCmdBaudrate.Controls.Add(this.htbGetIdentifier);
            this.gbCmdBaudrate.Controls.Add(this.htbSetIdentifier);
            this.gbCmdBaudrate.Controls.Add(this.btSetIdentifier);
            this.gbCmdBaudrate.Controls.Add(this.btGetIdentifier);
            this.gbCmdBaudrate.ForeColor = System.Drawing.Color.Black;
            this.gbCmdBaudrate.Name = "gbCmdBaudrate";
            this.gbCmdBaudrate.TabStop = false;
            // 
            // htbGetIdentifier
            // 
            resources.ApplyResources(this.htbGetIdentifier, "htbGetIdentifier");
            this.htbGetIdentifier.Name = "htbGetIdentifier";
            this.htbGetIdentifier.ReadOnly = true;
            // 
            // htbSetIdentifier
            // 
            resources.ApplyResources(this.htbSetIdentifier, "htbSetIdentifier");
            this.htbSetIdentifier.Name = "htbSetIdentifier";
            // 
            // btSetIdentifier
            // 
            resources.ApplyResources(this.btSetIdentifier, "btSetIdentifier");
            this.btSetIdentifier.Name = "btSetIdentifier";
            this.btSetIdentifier.UseVisualStyleBackColor = true;
            this.btSetIdentifier.Click += new System.EventHandler(this.btnSetIdentifier_Click);
            // 
            // btGetIdentifier
            // 
            resources.ApplyResources(this.btGetIdentifier, "btGetIdentifier");
            this.btGetIdentifier.Name = "btGetIdentifier";
            this.btGetIdentifier.UseVisualStyleBackColor = true;
            this.btGetIdentifier.Click += new System.EventHandler(this.btnGetIdentifier_Click);
            // 
            // btReaderSetupRefresh
            // 
            resources.ApplyResources(this.btReaderSetupRefresh, "btReaderSetupRefresh");
            this.btReaderSetupRefresh.Name = "btReaderSetupRefresh";
            this.btReaderSetupRefresh.UseVisualStyleBackColor = true;
            this.btReaderSetupRefresh.Click += new System.EventHandler(this.btnReaderSetupRefresh_Click);
            // 
            // gbCmdReadGpio
            // 
            resources.ApplyResources(this.gbCmdReadGpio, "gbCmdReadGpio");
            this.gbCmdReadGpio.Controls.Add(this.groupBox11);
            this.gbCmdReadGpio.Controls.Add(this.groupBox10);
            this.gbCmdReadGpio.ForeColor = System.Drawing.Color.Black;
            this.gbCmdReadGpio.Name = "gbCmdReadGpio";
            this.gbCmdReadGpio.TabStop = false;
            // 
            // groupBox11
            // 
            resources.ApplyResources(this.groupBox11, "groupBox11");
            this.groupBox11.BackColor = System.Drawing.Color.Transparent;
            this.groupBox11.Controls.Add(this.groupBox6);
            this.groupBox11.Controls.Add(this.groupBox7);
            this.groupBox11.Controls.Add(this.btnWriteGpio4Value);
            this.groupBox11.Controls.Add(this.btnWriteGpio3Value);
            this.groupBox11.ForeColor = System.Drawing.Color.Black;
            this.groupBox11.Name = "groupBox11";
            this.groupBox11.TabStop = false;
            // 
            // groupBox6
            // 
            resources.ApplyResources(this.groupBox6, "groupBox6");
            this.groupBox6.Controls.Add(this.label33);
            this.groupBox6.Controls.Add(this.rdbGpio3High);
            this.groupBox6.Controls.Add(this.rdbGpio3Low);
            this.groupBox6.Name = "groupBox6";
            this.groupBox6.TabStop = false;
            // 
            // label33
            // 
            resources.ApplyResources(this.label33, "label33");
            this.label33.Name = "label33";
            // 
            // rdbGpio3High
            // 
            resources.ApplyResources(this.rdbGpio3High, "rdbGpio3High");
            this.rdbGpio3High.Name = "rdbGpio3High";
            this.rdbGpio3High.TabStop = true;
            this.rdbGpio3High.UseVisualStyleBackColor = true;
            // 
            // rdbGpio3Low
            // 
            resources.ApplyResources(this.rdbGpio3Low, "rdbGpio3Low");
            this.rdbGpio3Low.Name = "rdbGpio3Low";
            this.rdbGpio3Low.TabStop = true;
            this.rdbGpio3Low.UseVisualStyleBackColor = true;
            // 
            // groupBox7
            // 
            resources.ApplyResources(this.groupBox7, "groupBox7");
            this.groupBox7.Controls.Add(this.label32);
            this.groupBox7.Controls.Add(this.rdbGpio4High);
            this.groupBox7.Controls.Add(this.rdbGpio4Low);
            this.groupBox7.Name = "groupBox7";
            this.groupBox7.TabStop = false;
            // 
            // label32
            // 
            resources.ApplyResources(this.label32, "label32");
            this.label32.Name = "label32";
            // 
            // rdbGpio4High
            // 
            resources.ApplyResources(this.rdbGpio4High, "rdbGpio4High");
            this.rdbGpio4High.Name = "rdbGpio4High";
            this.rdbGpio4High.TabStop = true;
            this.rdbGpio4High.UseVisualStyleBackColor = true;
            // 
            // rdbGpio4Low
            // 
            resources.ApplyResources(this.rdbGpio4Low, "rdbGpio4Low");
            this.rdbGpio4Low.Name = "rdbGpio4Low";
            this.rdbGpio4Low.TabStop = true;
            this.rdbGpio4Low.UseVisualStyleBackColor = true;
            // 
            // btnWriteGpio4Value
            // 
            resources.ApplyResources(this.btnWriteGpio4Value, "btnWriteGpio4Value");
            this.btnWriteGpio4Value.Name = "btnWriteGpio4Value";
            this.btnWriteGpio4Value.UseVisualStyleBackColor = true;
            this.btnWriteGpio4Value.Click += new System.EventHandler(this.btnWriteGpio4Value_Click);
            // 
            // btnWriteGpio3Value
            // 
            resources.ApplyResources(this.btnWriteGpio3Value, "btnWriteGpio3Value");
            this.btnWriteGpio3Value.Name = "btnWriteGpio3Value";
            this.btnWriteGpio3Value.UseVisualStyleBackColor = true;
            this.btnWriteGpio3Value.Click += new System.EventHandler(this.btnWriteGpio3Value_Click);
            // 
            // groupBox10
            // 
            resources.ApplyResources(this.groupBox10, "groupBox10");
            this.groupBox10.Controls.Add(this.groupBox4);
            this.groupBox10.Controls.Add(this.groupBox5);
            this.groupBox10.Controls.Add(this.btnReadGpioValue);
            this.groupBox10.ForeColor = System.Drawing.Color.Black;
            this.groupBox10.Name = "groupBox10";
            this.groupBox10.TabStop = false;
            // 
            // groupBox4
            // 
            resources.ApplyResources(this.groupBox4, "groupBox4");
            this.groupBox4.Controls.Add(this.label30);
            this.groupBox4.Controls.Add(this.rdbGpio1High);
            this.groupBox4.Controls.Add(this.rdbGpio1Low);
            this.groupBox4.Name = "groupBox4";
            this.groupBox4.TabStop = false;
            // 
            // label30
            // 
            resources.ApplyResources(this.label30, "label30");
            this.label30.Name = "label30";
            // 
            // rdbGpio1High
            // 
            resources.ApplyResources(this.rdbGpio1High, "rdbGpio1High");
            this.rdbGpio1High.Name = "rdbGpio1High";
            this.rdbGpio1High.TabStop = true;
            this.rdbGpio1High.UseVisualStyleBackColor = true;
            // 
            // rdbGpio1Low
            // 
            resources.ApplyResources(this.rdbGpio1Low, "rdbGpio1Low");
            this.rdbGpio1Low.Name = "rdbGpio1Low";
            this.rdbGpio1Low.TabStop = true;
            this.rdbGpio1Low.UseVisualStyleBackColor = true;
            // 
            // groupBox5
            // 
            resources.ApplyResources(this.groupBox5, "groupBox5");
            this.groupBox5.Controls.Add(this.label31);
            this.groupBox5.Controls.Add(this.rdbGpio2High);
            this.groupBox5.Controls.Add(this.rdbGpio2Low);
            this.groupBox5.Name = "groupBox5";
            this.groupBox5.TabStop = false;
            // 
            // label31
            // 
            resources.ApplyResources(this.label31, "label31");
            this.label31.Name = "label31";
            // 
            // rdbGpio2High
            // 
            resources.ApplyResources(this.rdbGpio2High, "rdbGpio2High");
            this.rdbGpio2High.Name = "rdbGpio2High";
            this.rdbGpio2High.TabStop = true;
            this.rdbGpio2High.UseVisualStyleBackColor = true;
            // 
            // rdbGpio2Low
            // 
            resources.ApplyResources(this.rdbGpio2Low, "rdbGpio2Low");
            this.rdbGpio2Low.Name = "rdbGpio2Low";
            this.rdbGpio2Low.TabStop = true;
            this.rdbGpio2Low.UseVisualStyleBackColor = true;
            // 
            // btnReadGpioValue
            // 
            resources.ApplyResources(this.btnReadGpioValue, "btnReadGpioValue");
            this.btnReadGpioValue.Name = "btnReadGpioValue";
            this.btnReadGpioValue.UseVisualStyleBackColor = true;
            this.btnReadGpioValue.Click += new System.EventHandler(this.btnReadGpioValue_Click);
            // 
            // gbCmdBeeper
            // 
            resources.ApplyResources(this.gbCmdBeeper, "gbCmdBeeper");
            this.gbCmdBeeper.Controls.Add(this.cbbBeepStatus);
            this.gbCmdBeeper.Controls.Add(this.btnSetBeeperMode);
            this.gbCmdBeeper.ForeColor = System.Drawing.Color.Black;
            this.gbCmdBeeper.Name = "gbCmdBeeper";
            this.gbCmdBeeper.TabStop = false;
            // 
            // cbbBeepStatus
            // 
            resources.ApplyResources(this.cbbBeepStatus, "cbbBeepStatus");
            this.cbbBeepStatus.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cbbBeepStatus.FormattingEnabled = true;
            this.cbbBeepStatus.Items.AddRange(new object[] {
            resources.GetString("cbbBeepStatus.Items"),
            resources.GetString("cbbBeepStatus.Items1"),
            resources.GetString("cbbBeepStatus.Items2")});
            this.cbbBeepStatus.Name = "cbbBeepStatus";
            // 
            // btnSetBeeperMode
            // 
            resources.ApplyResources(this.btnSetBeeperMode, "btnSetBeeperMode");
            this.btnSetBeeperMode.Name = "btnSetBeeperMode";
            this.btnSetBeeperMode.UseVisualStyleBackColor = true;
            this.btnSetBeeperMode.Click += new System.EventHandler(this.btnSetBeeperMode_Click);
            // 
            // gbCmdTemperature
            // 
            resources.ApplyResources(this.gbCmdTemperature, "gbCmdTemperature");
            this.gbCmdTemperature.Controls.Add(this.btnGetReaderTemperature);
            this.gbCmdTemperature.Controls.Add(this.txtReaderTemperature);
            this.gbCmdTemperature.ForeColor = System.Drawing.Color.Black;
            this.gbCmdTemperature.Name = "gbCmdTemperature";
            this.gbCmdTemperature.TabStop = false;
            // 
            // btnGetReaderTemperature
            // 
            resources.ApplyResources(this.btnGetReaderTemperature, "btnGetReaderTemperature");
            this.btnGetReaderTemperature.Name = "btnGetReaderTemperature";
            this.btnGetReaderTemperature.UseVisualStyleBackColor = true;
            this.btnGetReaderTemperature.Click += new System.EventHandler(this.btnGetReaderTemperature_Click);
            // 
            // txtReaderTemperature
            // 
            resources.ApplyResources(this.txtReaderTemperature, "txtReaderTemperature");
            this.txtReaderTemperature.Name = "txtReaderTemperature";
            this.txtReaderTemperature.ReadOnly = true;
            // 
            // gbCmdVersion
            // 
            resources.ApplyResources(this.gbCmdVersion, "gbCmdVersion");
            this.gbCmdVersion.Controls.Add(this.btnGetFirmwareVersion);
            this.gbCmdVersion.Controls.Add(this.txtFirmwareVersion);
            this.gbCmdVersion.ForeColor = System.Drawing.Color.Black;
            this.gbCmdVersion.Name = "gbCmdVersion";
            this.gbCmdVersion.TabStop = false;
            // 
            // btnGetFirmwareVersion
            // 
            resources.ApplyResources(this.btnGetFirmwareVersion, "btnGetFirmwareVersion");
            this.btnGetFirmwareVersion.Name = "btnGetFirmwareVersion";
            this.btnGetFirmwareVersion.UseVisualStyleBackColor = true;
            this.btnGetFirmwareVersion.Click += new System.EventHandler(this.btnGetFirmwareVersion_Click);
            // 
            // txtFirmwareVersion
            // 
            resources.ApplyResources(this.txtFirmwareVersion, "txtFirmwareVersion");
            this.txtFirmwareVersion.Name = "txtFirmwareVersion";
            this.txtFirmwareVersion.ReadOnly = true;
            // 
            // btnResetReader
            // 
            resources.ApplyResources(this.btnResetReader, "btnResetReader");
            this.btnResetReader.Name = "btnResetReader";
            this.btnResetReader.UseVisualStyleBackColor = true;
            this.btnResetReader.Click += new System.EventHandler(this.btnResetReader_Click);
            // 
            // tabPage2
            // 
            resources.ApplyResources(this.tabPage2, "tabPage2");
            this.tabPage2.BackColor = System.Drawing.Color.WhiteSmoke;
            this.tabPage2.Controls.Add(this.flowLayoutPanel3);
            this.tabPage2.Controls.Add(this.gbReturnLoss);
            this.tabPage2.Controls.Add(this.btRfSetup);
            this.tabPage2.Controls.Add(this.gbMonza);
            this.tabPage2.Controls.Add(this.gbCmdAntDetector);
            this.tabPage2.Controls.Add(this.gbCmdAntenna);
            this.tabPage2.Controls.Add(this.gbCmdOutputPower);
            this.tabPage2.Name = "tabPage2";
            // 
            // flowLayoutPanel3
            // 
            resources.ApplyResources(this.flowLayoutPanel3, "flowLayoutPanel3");
            this.flowLayoutPanel3.Controls.Add(this.gbCmdRegion);
            this.flowLayoutPanel3.Controls.Add(this.gbProfile);
            this.flowLayoutPanel3.Name = "flowLayoutPanel3";
            // 
            // gbCmdRegion
            // 
            resources.ApplyResources(this.gbCmdRegion, "gbCmdRegion");
            this.gbCmdRegion.Controls.Add(this.cbUserDefineFreq);
            this.gbCmdRegion.Controls.Add(this.groupBox23);
            this.gbCmdRegion.Controls.Add(this.groupBox21);
            this.gbCmdRegion.Controls.Add(this.btnGetFrequencyRegion);
            this.gbCmdRegion.Controls.Add(this.btnSetFrequencyRegion);
            this.gbCmdRegion.ForeColor = System.Drawing.Color.Black;
            this.gbCmdRegion.Name = "gbCmdRegion";
            this.gbCmdRegion.TabStop = false;
            // 
            // cbUserDefineFreq
            // 
            resources.ApplyResources(this.cbUserDefineFreq, "cbUserDefineFreq");
            this.cbUserDefineFreq.Name = "cbUserDefineFreq";
            this.cbUserDefineFreq.UseVisualStyleBackColor = true;
            this.cbUserDefineFreq.CheckedChanged += new System.EventHandler(this.cbUserDefineFreq_CheckedChanged);
            // 
            // groupBox23
            // 
            resources.ApplyResources(this.groupBox23, "groupBox23");
            this.groupBox23.Controls.Add(this.label106);
            this.groupBox23.Controls.Add(this.label105);
            this.groupBox23.Controls.Add(this.label104);
            this.groupBox23.Controls.Add(this.label103);
            this.groupBox23.Controls.Add(this.label86);
            this.groupBox23.Controls.Add(this.label75);
            this.groupBox23.Controls.Add(this.textFreqQuantity);
            this.groupBox23.Controls.Add(this.TextFreqInterval);
            this.groupBox23.Controls.Add(this.textStartFreq);
            this.groupBox23.ForeColor = System.Drawing.Color.Black;
            this.groupBox23.Name = "groupBox23";
            this.groupBox23.TabStop = false;
            // 
            // label106
            // 
            resources.ApplyResources(this.label106, "label106");
            this.label106.Name = "label106";
            // 
            // label105
            // 
            resources.ApplyResources(this.label105, "label105");
            this.label105.Name = "label105";
            // 
            // label104
            // 
            resources.ApplyResources(this.label104, "label104");
            this.label104.Name = "label104";
            // 
            // label103
            // 
            resources.ApplyResources(this.label103, "label103");
            this.label103.Name = "label103";
            // 
            // label86
            // 
            resources.ApplyResources(this.label86, "label86");
            this.label86.Name = "label86";
            // 
            // label75
            // 
            resources.ApplyResources(this.label75, "label75");
            this.label75.Name = "label75";
            // 
            // textFreqQuantity
            // 
            resources.ApplyResources(this.textFreqQuantity, "textFreqQuantity");
            this.textFreqQuantity.Name = "textFreqQuantity";
            // 
            // TextFreqInterval
            // 
            resources.ApplyResources(this.TextFreqInterval, "TextFreqInterval");
            this.TextFreqInterval.Name = "TextFreqInterval";
            // 
            // textStartFreq
            // 
            resources.ApplyResources(this.textStartFreq, "textStartFreq");
            this.textStartFreq.Name = "textStartFreq";
            // 
            // groupBox21
            // 
            resources.ApplyResources(this.groupBox21, "groupBox21");
            this.groupBox21.Controls.Add(this.label37);
            this.groupBox21.Controls.Add(this.label36);
            this.groupBox21.Controls.Add(this.cmbFrequencyEnd);
            this.groupBox21.Controls.Add(this.label13);
            this.groupBox21.Controls.Add(this.cmbFrequencyStart);
            this.groupBox21.Controls.Add(this.label12);
            this.groupBox21.Controls.Add(this.rdbRegionChn);
            this.groupBox21.Controls.Add(this.rdbRegionEtsi);
            this.groupBox21.Controls.Add(this.rdbRegionFcc);
            this.groupBox21.ForeColor = System.Drawing.Color.Black;
            this.groupBox21.Name = "groupBox21";
            this.groupBox21.TabStop = false;
            // 
            // label37
            // 
            resources.ApplyResources(this.label37, "label37");
            this.label37.Name = "label37";
            // 
            // label36
            // 
            resources.ApplyResources(this.label36, "label36");
            this.label36.Name = "label36";
            // 
            // cmbFrequencyEnd
            // 
            resources.ApplyResources(this.cmbFrequencyEnd, "cmbFrequencyEnd");
            this.cmbFrequencyEnd.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbFrequencyEnd.FormattingEnabled = true;
            this.cmbFrequencyEnd.Name = "cmbFrequencyEnd";
            // 
            // label13
            // 
            resources.ApplyResources(this.label13, "label13");
            this.label13.Name = "label13";
            // 
            // cmbFrequencyStart
            // 
            resources.ApplyResources(this.cmbFrequencyStart, "cmbFrequencyStart");
            this.cmbFrequencyStart.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbFrequencyStart.FormattingEnabled = true;
            this.cmbFrequencyStart.Name = "cmbFrequencyStart";
            // 
            // label12
            // 
            resources.ApplyResources(this.label12, "label12");
            this.label12.Name = "label12";
            // 
            // rdbRegionChn
            // 
            resources.ApplyResources(this.rdbRegionChn, "rdbRegionChn");
            this.rdbRegionChn.Name = "rdbRegionChn";
            this.rdbRegionChn.TabStop = true;
            this.rdbRegionChn.UseVisualStyleBackColor = true;
            this.rdbRegionChn.CheckedChanged += new System.EventHandler(this.rdbRegionChn_CheckedChanged);
            // 
            // rdbRegionEtsi
            // 
            resources.ApplyResources(this.rdbRegionEtsi, "rdbRegionEtsi");
            this.rdbRegionEtsi.Name = "rdbRegionEtsi";
            this.rdbRegionEtsi.TabStop = true;
            this.rdbRegionEtsi.UseVisualStyleBackColor = true;
            this.rdbRegionEtsi.CheckedChanged += new System.EventHandler(this.rdbRegionEtsi_CheckedChanged);
            // 
            // rdbRegionFcc
            // 
            resources.ApplyResources(this.rdbRegionFcc, "rdbRegionFcc");
            this.rdbRegionFcc.Name = "rdbRegionFcc";
            this.rdbRegionFcc.TabStop = true;
            this.rdbRegionFcc.UseVisualStyleBackColor = true;
            this.rdbRegionFcc.CheckedChanged += new System.EventHandler(this.rdbRegionFcc_CheckedChanged);
            // 
            // btnGetFrequencyRegion
            // 
            resources.ApplyResources(this.btnGetFrequencyRegion, "btnGetFrequencyRegion");
            this.btnGetFrequencyRegion.Name = "btnGetFrequencyRegion";
            this.btnGetFrequencyRegion.UseVisualStyleBackColor = true;
            this.btnGetFrequencyRegion.Click += new System.EventHandler(this.btnGetFrequencyRegion_Click);
            // 
            // btnSetFrequencyRegion
            // 
            resources.ApplyResources(this.btnSetFrequencyRegion, "btnSetFrequencyRegion");
            this.btnSetFrequencyRegion.Name = "btnSetFrequencyRegion";
            this.btnSetFrequencyRegion.UseVisualStyleBackColor = true;
            this.btnSetFrequencyRegion.Click += new System.EventHandler(this.btnSetFrequencyRegion_Click);
            // 
            // gbProfile
            // 
            resources.ApplyResources(this.gbProfile, "gbProfile");
            this.gbProfile.Controls.Add(this.label19);
            this.gbProfile.Controls.Add(this.cmbModuleLink);
            this.gbProfile.Controls.Add(this.btGetProfile);
            this.gbProfile.Controls.Add(this.btSetProfile);
            this.gbProfile.ForeColor = System.Drawing.Color.Black;
            this.gbProfile.Name = "gbProfile";
            this.gbProfile.TabStop = false;
            // 
            // label19
            // 
            resources.ApplyResources(this.label19, "label19");
            this.label19.Name = "label19";
            // 
            // cmbModuleLink
            // 
            resources.ApplyResources(this.cmbModuleLink, "cmbModuleLink");
            this.cmbModuleLink.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbModuleLink.FormattingEnabled = true;
            this.cmbModuleLink.Items.AddRange(new object[] {
            resources.GetString("cmbModuleLink.Items"),
            resources.GetString("cmbModuleLink.Items1"),
            resources.GetString("cmbModuleLink.Items2"),
            resources.GetString("cmbModuleLink.Items3")});
            this.cmbModuleLink.Name = "cmbModuleLink";
            // 
            // btGetProfile
            // 
            resources.ApplyResources(this.btGetProfile, "btGetProfile");
            this.btGetProfile.Name = "btGetProfile";
            this.btGetProfile.UseVisualStyleBackColor = true;
            this.btGetProfile.Click += new System.EventHandler(this.btGetProfile_Click);
            // 
            // btSetProfile
            // 
            resources.ApplyResources(this.btSetProfile, "btSetProfile");
            this.btSetProfile.Name = "btSetProfile";
            this.btSetProfile.UseVisualStyleBackColor = true;
            this.btSetProfile.Click += new System.EventHandler(this.btSetProfile_Click);
            // 
            // gbReturnLoss
            // 
            resources.ApplyResources(this.gbReturnLoss, "gbReturnLoss");
            this.gbReturnLoss.BackColor = System.Drawing.Color.Transparent;
            this.gbReturnLoss.Controls.Add(this.label110);
            this.gbReturnLoss.Controls.Add(this.label109);
            this.gbReturnLoss.Controls.Add(this.cmbReturnLossFreq);
            this.gbReturnLoss.Controls.Add(this.label108);
            this.gbReturnLoss.Controls.Add(this.textReturnLoss);
            this.gbReturnLoss.Controls.Add(this.btReturnLoss);
            this.gbReturnLoss.ForeColor = System.Drawing.Color.Black;
            this.gbReturnLoss.Name = "gbReturnLoss";
            this.gbReturnLoss.TabStop = false;
            // 
            // label110
            // 
            resources.ApplyResources(this.label110, "label110");
            this.label110.Name = "label110";
            // 
            // label109
            // 
            resources.ApplyResources(this.label109, "label109");
            this.label109.Name = "label109";
            // 
            // cmbReturnLossFreq
            // 
            resources.ApplyResources(this.cmbReturnLossFreq, "cmbReturnLossFreq");
            this.cmbReturnLossFreq.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbReturnLossFreq.FormattingEnabled = true;
            this.cmbReturnLossFreq.Items.AddRange(new object[] {
            resources.GetString("cmbReturnLossFreq.Items"),
            resources.GetString("cmbReturnLossFreq.Items1"),
            resources.GetString("cmbReturnLossFreq.Items2"),
            resources.GetString("cmbReturnLossFreq.Items3"),
            resources.GetString("cmbReturnLossFreq.Items4"),
            resources.GetString("cmbReturnLossFreq.Items5"),
            resources.GetString("cmbReturnLossFreq.Items6"),
            resources.GetString("cmbReturnLossFreq.Items7"),
            resources.GetString("cmbReturnLossFreq.Items8"),
            resources.GetString("cmbReturnLossFreq.Items9"),
            resources.GetString("cmbReturnLossFreq.Items10"),
            resources.GetString("cmbReturnLossFreq.Items11"),
            resources.GetString("cmbReturnLossFreq.Items12"),
            resources.GetString("cmbReturnLossFreq.Items13"),
            resources.GetString("cmbReturnLossFreq.Items14"),
            resources.GetString("cmbReturnLossFreq.Items15"),
            resources.GetString("cmbReturnLossFreq.Items16"),
            resources.GetString("cmbReturnLossFreq.Items17"),
            resources.GetString("cmbReturnLossFreq.Items18"),
            resources.GetString("cmbReturnLossFreq.Items19"),
            resources.GetString("cmbReturnLossFreq.Items20"),
            resources.GetString("cmbReturnLossFreq.Items21"),
            resources.GetString("cmbReturnLossFreq.Items22"),
            resources.GetString("cmbReturnLossFreq.Items23"),
            resources.GetString("cmbReturnLossFreq.Items24"),
            resources.GetString("cmbReturnLossFreq.Items25"),
            resources.GetString("cmbReturnLossFreq.Items26"),
            resources.GetString("cmbReturnLossFreq.Items27"),
            resources.GetString("cmbReturnLossFreq.Items28"),
            resources.GetString("cmbReturnLossFreq.Items29"),
            resources.GetString("cmbReturnLossFreq.Items30"),
            resources.GetString("cmbReturnLossFreq.Items31"),
            resources.GetString("cmbReturnLossFreq.Items32"),
            resources.GetString("cmbReturnLossFreq.Items33"),
            resources.GetString("cmbReturnLossFreq.Items34"),
            resources.GetString("cmbReturnLossFreq.Items35"),
            resources.GetString("cmbReturnLossFreq.Items36"),
            resources.GetString("cmbReturnLossFreq.Items37"),
            resources.GetString("cmbReturnLossFreq.Items38"),
            resources.GetString("cmbReturnLossFreq.Items39"),
            resources.GetString("cmbReturnLossFreq.Items40"),
            resources.GetString("cmbReturnLossFreq.Items41"),
            resources.GetString("cmbReturnLossFreq.Items42"),
            resources.GetString("cmbReturnLossFreq.Items43"),
            resources.GetString("cmbReturnLossFreq.Items44"),
            resources.GetString("cmbReturnLossFreq.Items45"),
            resources.GetString("cmbReturnLossFreq.Items46"),
            resources.GetString("cmbReturnLossFreq.Items47"),
            resources.GetString("cmbReturnLossFreq.Items48"),
            resources.GetString("cmbReturnLossFreq.Items49"),
            resources.GetString("cmbReturnLossFreq.Items50"),
            resources.GetString("cmbReturnLossFreq.Items51"),
            resources.GetString("cmbReturnLossFreq.Items52"),
            resources.GetString("cmbReturnLossFreq.Items53"),
            resources.GetString("cmbReturnLossFreq.Items54"),
            resources.GetString("cmbReturnLossFreq.Items55"),
            resources.GetString("cmbReturnLossFreq.Items56"),
            resources.GetString("cmbReturnLossFreq.Items57"),
            resources.GetString("cmbReturnLossFreq.Items58"),
            resources.GetString("cmbReturnLossFreq.Items59")});
            this.cmbReturnLossFreq.Name = "cmbReturnLossFreq";
            // 
            // label108
            // 
            resources.ApplyResources(this.label108, "label108");
            this.label108.Name = "label108";
            // 
            // textReturnLoss
            // 
            resources.ApplyResources(this.textReturnLoss, "textReturnLoss");
            this.textReturnLoss.Name = "textReturnLoss";
            this.textReturnLoss.ReadOnly = true;
            // 
            // btReturnLoss
            // 
            resources.ApplyResources(this.btReturnLoss, "btReturnLoss");
            this.btReturnLoss.Name = "btReturnLoss";
            this.btReturnLoss.UseVisualStyleBackColor = true;
            this.btReturnLoss.Click += new System.EventHandler(this.btnReturnLoss_Click);
            // 
            // btRfSetup
            // 
            resources.ApplyResources(this.btRfSetup, "btRfSetup");
            this.btRfSetup.Name = "btRfSetup";
            this.btRfSetup.UseVisualStyleBackColor = true;
            this.btRfSetup.Click += new System.EventHandler(this.btnRfSetup_Click);
            // 
            // gbMonza
            // 
            resources.ApplyResources(this.gbMonza, "gbMonza");
            this.gbMonza.Controls.Add(this.label14);
            this.gbMonza.Controls.Add(this.label11);
            this.gbMonza.Controls.Add(this.rdbMonzaOff);
            this.gbMonza.Controls.Add(this.btSetMonzaStatus);
            this.gbMonza.Controls.Add(this.btGetMonzaStatus);
            this.gbMonza.Controls.Add(this.rdbMonzaOn);
            this.gbMonza.ForeColor = System.Drawing.Color.Black;
            this.gbMonza.Name = "gbMonza";
            this.gbMonza.TabStop = false;
            // 
            // label14
            // 
            resources.ApplyResources(this.label14, "label14");
            this.label14.ForeColor = System.Drawing.Color.CornflowerBlue;
            this.label14.Name = "label14";
            // 
            // label11
            // 
            resources.ApplyResources(this.label11, "label11");
            this.label11.ForeColor = System.Drawing.Color.CornflowerBlue;
            this.label11.Name = "label11";
            // 
            // rdbMonzaOff
            // 
            resources.ApplyResources(this.rdbMonzaOff, "rdbMonzaOff");
            this.rdbMonzaOff.Name = "rdbMonzaOff";
            this.rdbMonzaOff.TabStop = true;
            this.rdbMonzaOff.UseVisualStyleBackColor = true;
            // 
            // btSetMonzaStatus
            // 
            resources.ApplyResources(this.btSetMonzaStatus, "btSetMonzaStatus");
            this.btSetMonzaStatus.Name = "btSetMonzaStatus";
            this.btSetMonzaStatus.UseVisualStyleBackColor = true;
            this.btSetMonzaStatus.Click += new System.EventHandler(this.btnSetMonzaStatus_Click);
            // 
            // btGetMonzaStatus
            // 
            resources.ApplyResources(this.btGetMonzaStatus, "btGetMonzaStatus");
            this.btGetMonzaStatus.Name = "btGetMonzaStatus";
            this.btGetMonzaStatus.UseVisualStyleBackColor = true;
            this.btGetMonzaStatus.Click += new System.EventHandler(this.btnGetMonzaStatus_Click);
            // 
            // rdbMonzaOn
            // 
            resources.ApplyResources(this.rdbMonzaOn, "rdbMonzaOn");
            this.rdbMonzaOn.Name = "rdbMonzaOn";
            this.rdbMonzaOn.TabStop = true;
            this.rdbMonzaOn.UseVisualStyleBackColor = true;
            // 
            // gbCmdAntDetector
            // 
            resources.ApplyResources(this.gbCmdAntDetector, "gbCmdAntDetector");
            this.gbCmdAntDetector.Controls.Add(this.label7);
            this.gbCmdAntDetector.Controls.Add(this.label6);
            this.gbCmdAntDetector.Controls.Add(this.label5);
            this.gbCmdAntDetector.Controls.Add(this.label10);
            this.gbCmdAntDetector.Controls.Add(this.label8);
            this.gbCmdAntDetector.Controls.Add(this.tbAntDectector);
            this.gbCmdAntDetector.Controls.Add(this.btnGetAntDetector);
            this.gbCmdAntDetector.Controls.Add(this.btnSetAntDetector);
            this.gbCmdAntDetector.ForeColor = System.Drawing.Color.Black;
            this.gbCmdAntDetector.Name = "gbCmdAntDetector";
            this.gbCmdAntDetector.TabStop = false;
            // 
            // label7
            // 
            resources.ApplyResources(this.label7, "label7");
            this.label7.ForeColor = System.Drawing.Color.CornflowerBlue;
            this.label7.Name = "label7";
            // 
            // label6
            // 
            resources.ApplyResources(this.label6, "label6");
            this.label6.ForeColor = System.Drawing.Color.CornflowerBlue;
            this.label6.Name = "label6";
            // 
            // label5
            // 
            resources.ApplyResources(this.label5, "label5");
            this.label5.ForeColor = System.Drawing.Color.CornflowerBlue;
            this.label5.Name = "label5";
            // 
            // label10
            // 
            resources.ApplyResources(this.label10, "label10");
            this.label10.Name = "label10";
            // 
            // label8
            // 
            resources.ApplyResources(this.label8, "label8");
            this.label8.Name = "label8";
            // 
            // tbAntDectector
            // 
            resources.ApplyResources(this.tbAntDectector, "tbAntDectector");
            this.tbAntDectector.Name = "tbAntDectector";
            // 
            // btnGetAntDetector
            // 
            resources.ApplyResources(this.btnGetAntDetector, "btnGetAntDetector");
            this.btnGetAntDetector.Name = "btnGetAntDetector";
            this.btnGetAntDetector.UseVisualStyleBackColor = true;
            this.btnGetAntDetector.Click += new System.EventHandler(this.btnGetAntDetector_Click);
            // 
            // btnSetAntDetector
            // 
            resources.ApplyResources(this.btnSetAntDetector, "btnSetAntDetector");
            this.btnSetAntDetector.Name = "btnSetAntDetector";
            this.btnSetAntDetector.UseVisualStyleBackColor = true;
            this.btnSetAntDetector.Click += new System.EventHandler(this.btnSetAntDetector_Click);
            // 
            // gbCmdAntenna
            // 
            resources.ApplyResources(this.gbCmdAntenna, "gbCmdAntenna");
            this.gbCmdAntenna.Controls.Add(this.label107);
            this.gbCmdAntenna.Controls.Add(this.cmbWorkAnt);
            this.gbCmdAntenna.Controls.Add(this.btnGetWorkAntenna);
            this.gbCmdAntenna.Controls.Add(this.btnSetWorkAntenna);
            this.gbCmdAntenna.ForeColor = System.Drawing.Color.Black;
            this.gbCmdAntenna.Name = "gbCmdAntenna";
            this.gbCmdAntenna.TabStop = false;
            // 
            // label107
            // 
            resources.ApplyResources(this.label107, "label107");
            this.label107.Name = "label107";
            // 
            // cmbWorkAnt
            // 
            resources.ApplyResources(this.cmbWorkAnt, "cmbWorkAnt");
            this.cmbWorkAnt.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbWorkAnt.FormattingEnabled = true;
            this.cmbWorkAnt.Items.AddRange(new object[] {
            resources.GetString("cmbWorkAnt.Items"),
            resources.GetString("cmbWorkAnt.Items1"),
            resources.GetString("cmbWorkAnt.Items2"),
            resources.GetString("cmbWorkAnt.Items3")});
            this.cmbWorkAnt.Name = "cmbWorkAnt";
            // 
            // btnGetWorkAntenna
            // 
            resources.ApplyResources(this.btnGetWorkAntenna, "btnGetWorkAntenna");
            this.btnGetWorkAntenna.Name = "btnGetWorkAntenna";
            this.btnGetWorkAntenna.UseVisualStyleBackColor = true;
            this.btnGetWorkAntenna.Click += new System.EventHandler(this.btnGetWorkAntenna_Click);
            // 
            // btnSetWorkAntenna
            // 
            resources.ApplyResources(this.btnSetWorkAntenna, "btnSetWorkAntenna");
            this.btnSetWorkAntenna.Name = "btnSetWorkAntenna";
            this.btnSetWorkAntenna.UseVisualStyleBackColor = true;
            this.btnSetWorkAntenna.Click += new System.EventHandler(this.btnSetWorkAntenna_Click);
            // 
            // gbCmdOutputPower
            // 
            resources.ApplyResources(this.gbCmdOutputPower, "gbCmdOutputPower");
            this.gbCmdOutputPower.Controls.Add(this.label151);
            this.gbCmdOutputPower.Controls.Add(this.label152);
            this.gbCmdOutputPower.Controls.Add(this.label153);
            this.gbCmdOutputPower.Controls.Add(this.label154);
            this.gbCmdOutputPower.Controls.Add(this.tb_outputpower_16);
            this.gbCmdOutputPower.Controls.Add(this.tb_outputpower_15);
            this.gbCmdOutputPower.Controls.Add(this.tb_outputpower_14);
            this.gbCmdOutputPower.Controls.Add(this.tb_outputpower_13);
            this.gbCmdOutputPower.Controls.Add(this.label147);
            this.gbCmdOutputPower.Controls.Add(this.label148);
            this.gbCmdOutputPower.Controls.Add(this.label149);
            this.gbCmdOutputPower.Controls.Add(this.label150);
            this.gbCmdOutputPower.Controls.Add(this.tb_outputpower_12);
            this.gbCmdOutputPower.Controls.Add(this.tb_outputpower_11);
            this.gbCmdOutputPower.Controls.Add(this.tb_outputpower_10);
            this.gbCmdOutputPower.Controls.Add(this.tb_outputpower_9);
            this.gbCmdOutputPower.Controls.Add(this.label115);
            this.gbCmdOutputPower.Controls.Add(this.label114);
            this.gbCmdOutputPower.Controls.Add(this.label113);
            this.gbCmdOutputPower.Controls.Add(this.label112);
            this.gbCmdOutputPower.Controls.Add(this.tb_outputpower_8);
            this.gbCmdOutputPower.Controls.Add(this.tb_outputpower_7);
            this.gbCmdOutputPower.Controls.Add(this.tb_outputpower_6);
            this.gbCmdOutputPower.Controls.Add(this.tb_outputpower_5);
            this.gbCmdOutputPower.Controls.Add(this.label34);
            this.gbCmdOutputPower.Controls.Add(this.label21);
            this.gbCmdOutputPower.Controls.Add(this.label20);
            this.gbCmdOutputPower.Controls.Add(this.label18);
            this.gbCmdOutputPower.Controls.Add(this.tb_outputpower_4);
            this.gbCmdOutputPower.Controls.Add(this.tb_outputpower_3);
            this.gbCmdOutputPower.Controls.Add(this.tb_outputpower_2);
            this.gbCmdOutputPower.Controls.Add(this.tb_outputpower_1);
            this.gbCmdOutputPower.Controls.Add(this.label15);
            this.gbCmdOutputPower.Controls.Add(this.btnGetOutputPower);
            this.gbCmdOutputPower.Controls.Add(this.btnSetOutputPower);
            this.gbCmdOutputPower.Controls.Add(this.label9);
            this.gbCmdOutputPower.ForeColor = System.Drawing.Color.Black;
            this.gbCmdOutputPower.Name = "gbCmdOutputPower";
            this.gbCmdOutputPower.TabStop = false;
            // 
            // label151
            // 
            resources.ApplyResources(this.label151, "label151");
            this.label151.Name = "label151";
            // 
            // label152
            // 
            resources.ApplyResources(this.label152, "label152");
            this.label152.Name = "label152";
            // 
            // label153
            // 
            resources.ApplyResources(this.label153, "label153");
            this.label153.Name = "label153";
            // 
            // label154
            // 
            resources.ApplyResources(this.label154, "label154");
            this.label154.Name = "label154";
            // 
            // tb_outputpower_16
            // 
            resources.ApplyResources(this.tb_outputpower_16, "tb_outputpower_16");
            this.tb_outputpower_16.Name = "tb_outputpower_16";
            this.tb_outputpower_16.TextChanged += new System.EventHandler(this.tb_outputpower_16_TextChanged);
            // 
            // tb_outputpower_15
            // 
            resources.ApplyResources(this.tb_outputpower_15, "tb_outputpower_15");
            this.tb_outputpower_15.Name = "tb_outputpower_15";
            this.tb_outputpower_15.TextChanged += new System.EventHandler(this.tb_outputpower_15_TextChanged);
            // 
            // tb_outputpower_14
            // 
            resources.ApplyResources(this.tb_outputpower_14, "tb_outputpower_14");
            this.tb_outputpower_14.Name = "tb_outputpower_14";
            this.tb_outputpower_14.TextChanged += new System.EventHandler(this.tb_outputpower_14_TextChanged);
            // 
            // tb_outputpower_13
            // 
            resources.ApplyResources(this.tb_outputpower_13, "tb_outputpower_13");
            this.tb_outputpower_13.Name = "tb_outputpower_13";
            this.tb_outputpower_13.TextChanged += new System.EventHandler(this.tb_outputpower_13_TextChanged);
            // 
            // label147
            // 
            resources.ApplyResources(this.label147, "label147");
            this.label147.Name = "label147";
            // 
            // label148
            // 
            resources.ApplyResources(this.label148, "label148");
            this.label148.Name = "label148";
            // 
            // label149
            // 
            resources.ApplyResources(this.label149, "label149");
            this.label149.Name = "label149";
            // 
            // label150
            // 
            resources.ApplyResources(this.label150, "label150");
            this.label150.Name = "label150";
            // 
            // tb_outputpower_12
            // 
            resources.ApplyResources(this.tb_outputpower_12, "tb_outputpower_12");
            this.tb_outputpower_12.Name = "tb_outputpower_12";
            this.tb_outputpower_12.TextChanged += new System.EventHandler(this.tb_outputpower_12_TextChanged);
            // 
            // tb_outputpower_11
            // 
            resources.ApplyResources(this.tb_outputpower_11, "tb_outputpower_11");
            this.tb_outputpower_11.Name = "tb_outputpower_11";
            this.tb_outputpower_11.TextChanged += new System.EventHandler(this.tb_outputpower_11_TextChanged);
            // 
            // tb_outputpower_10
            // 
            resources.ApplyResources(this.tb_outputpower_10, "tb_outputpower_10");
            this.tb_outputpower_10.Name = "tb_outputpower_10";
            this.tb_outputpower_10.TextChanged += new System.EventHandler(this.tb_outputpower_10_TextChanged);
            // 
            // tb_outputpower_9
            // 
            resources.ApplyResources(this.tb_outputpower_9, "tb_outputpower_9");
            this.tb_outputpower_9.Name = "tb_outputpower_9";
            this.tb_outputpower_9.TextChanged += new System.EventHandler(this.tb_outputpower_9_TextChanged);
            // 
            // label115
            // 
            resources.ApplyResources(this.label115, "label115");
            this.label115.Name = "label115";
            // 
            // label114
            // 
            resources.ApplyResources(this.label114, "label114");
            this.label114.Name = "label114";
            // 
            // label113
            // 
            resources.ApplyResources(this.label113, "label113");
            this.label113.Name = "label113";
            // 
            // label112
            // 
            resources.ApplyResources(this.label112, "label112");
            this.label112.Name = "label112";
            // 
            // tb_outputpower_8
            // 
            resources.ApplyResources(this.tb_outputpower_8, "tb_outputpower_8");
            this.tb_outputpower_8.Name = "tb_outputpower_8";
            this.tb_outputpower_8.TextChanged += new System.EventHandler(this.textBox10_TextChanged);
            // 
            // tb_outputpower_7
            // 
            resources.ApplyResources(this.tb_outputpower_7, "tb_outputpower_7");
            this.tb_outputpower_7.Name = "tb_outputpower_7";
            this.tb_outputpower_7.TextChanged += new System.EventHandler(this.textBox9_TextChanged);
            // 
            // tb_outputpower_6
            // 
            resources.ApplyResources(this.tb_outputpower_6, "tb_outputpower_6");
            this.tb_outputpower_6.Name = "tb_outputpower_6";
            this.tb_outputpower_6.TextChanged += new System.EventHandler(this.textBox8_TextChanged);
            // 
            // tb_outputpower_5
            // 
            resources.ApplyResources(this.tb_outputpower_5, "tb_outputpower_5");
            this.tb_outputpower_5.Name = "tb_outputpower_5";
            this.tb_outputpower_5.TextChanged += new System.EventHandler(this.textBox7_TextChanged);
            // 
            // label34
            // 
            resources.ApplyResources(this.label34, "label34");
            this.label34.Name = "label34";
            // 
            // label21
            // 
            resources.ApplyResources(this.label21, "label21");
            this.label21.Name = "label21";
            // 
            // label20
            // 
            resources.ApplyResources(this.label20, "label20");
            this.label20.Name = "label20";
            // 
            // label18
            // 
            resources.ApplyResources(this.label18, "label18");
            this.label18.Name = "label18";
            // 
            // tb_outputpower_4
            // 
            resources.ApplyResources(this.tb_outputpower_4, "tb_outputpower_4");
            this.tb_outputpower_4.Name = "tb_outputpower_4";
            this.tb_outputpower_4.TextChanged += new System.EventHandler(this.textBox4_TextChanged);
            // 
            // tb_outputpower_3
            // 
            resources.ApplyResources(this.tb_outputpower_3, "tb_outputpower_3");
            this.tb_outputpower_3.Name = "tb_outputpower_3";
            this.tb_outputpower_3.TextChanged += new System.EventHandler(this.textBox3_TextChanged);
            // 
            // tb_outputpower_2
            // 
            resources.ApplyResources(this.tb_outputpower_2, "tb_outputpower_2");
            this.tb_outputpower_2.Name = "tb_outputpower_2";
            this.tb_outputpower_2.TextChanged += new System.EventHandler(this.textBox2_TextChanged);
            // 
            // tb_outputpower_1
            // 
            resources.ApplyResources(this.tb_outputpower_1, "tb_outputpower_1");
            this.tb_outputpower_1.Name = "tb_outputpower_1";
            this.tb_outputpower_1.TextChanged += new System.EventHandler(this.textBox1_TextChanged);
            // 
            // label15
            // 
            resources.ApplyResources(this.label15, "label15");
            this.label15.Name = "label15";
            // 
            // btnGetOutputPower
            // 
            resources.ApplyResources(this.btnGetOutputPower, "btnGetOutputPower");
            this.btnGetOutputPower.Name = "btnGetOutputPower";
            this.btnGetOutputPower.UseVisualStyleBackColor = true;
            this.btnGetOutputPower.Click += new System.EventHandler(this.btnGetOutputPower_Click);
            // 
            // btnSetOutputPower
            // 
            resources.ApplyResources(this.btnSetOutputPower, "btnSetOutputPower");
            this.btnSetOutputPower.Name = "btnSetOutputPower";
            this.btnSetOutputPower.UseVisualStyleBackColor = true;
            this.btnSetOutputPower.Click += new System.EventHandler(this.btnSetOutputPower_Click);
            // 
            // label9
            // 
            resources.ApplyResources(this.label9, "label9");
            this.label9.Name = "label9";
            // 
            // tabPage4
            // 
            resources.ApplyResources(this.tabPage4, "tabPage4");
            this.tabPage4.BackColor = System.Drawing.Color.WhiteSmoke;
            this.tabPage4.Controls.Add(this.btE710Refresh);
            this.tabPage4.Controls.Add(this.flowLayoutPanel4);
            this.tabPage4.Name = "tabPage4";
            // 
            // btE710Refresh
            // 
            resources.ApplyResources(this.btE710Refresh, "btE710Refresh");
            this.btE710Refresh.Name = "btE710Refresh";
            this.btE710Refresh.UseVisualStyleBackColor = true;
            this.btE710Refresh.Click += new System.EventHandler(this.btE710Refresh_Click);
            // 
            // flowLayoutPanel4
            // 
            resources.ApplyResources(this.flowLayoutPanel4, "flowLayoutPanel4");
            this.flowLayoutPanel4.Controls.Add(this.gbRfLink);
            this.flowLayoutPanel4.Controls.Add(this.grpbQ);
            this.flowLayoutPanel4.Controls.Add(this.groupBox32);
            this.flowLayoutPanel4.Name = "flowLayoutPanel4";
            // 
            // gbRfLink
            // 
            resources.ApplyResources(this.gbRfLink, "gbRfLink");
            this.gbRfLink.Controls.Add(this.btSetE710Profile);
            this.gbRfLink.Controls.Add(this.btGetE710Profile);
            this.gbRfLink.Controls.Add(this.cbbE710RfLink);
            this.gbRfLink.Controls.Add(this.label40);
            this.gbRfLink.Controls.Add(this.cbDrmSwich);
            this.gbRfLink.Name = "gbRfLink";
            this.gbRfLink.TabStop = false;
            // 
            // btSetE710Profile
            // 
            resources.ApplyResources(this.btSetE710Profile, "btSetE710Profile");
            this.btSetE710Profile.Name = "btSetE710Profile";
            this.btSetE710Profile.UseVisualStyleBackColor = true;
            this.btSetE710Profile.Click += new System.EventHandler(this.btSetE710Profile_Click);
            // 
            // btGetE710Profile
            // 
            resources.ApplyResources(this.btGetE710Profile, "btGetE710Profile");
            this.btGetE710Profile.Name = "btGetE710Profile";
            this.btGetE710Profile.UseVisualStyleBackColor = true;
            this.btGetE710Profile.Click += new System.EventHandler(this.btGetE710Profile_Click);
            // 
            // cbbE710RfLink
            // 
            resources.ApplyResources(this.cbbE710RfLink, "cbbE710RfLink");
            this.cbbE710RfLink.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cbbE710RfLink.FormattingEnabled = true;
            this.cbbE710RfLink.Items.AddRange(new object[] {
            resources.GetString("cbbE710RfLink.Items"),
            resources.GetString("cbbE710RfLink.Items1"),
            resources.GetString("cbbE710RfLink.Items2"),
            resources.GetString("cbbE710RfLink.Items3")});
            this.cbbE710RfLink.Name = "cbbE710RfLink";
            // 
            // label40
            // 
            resources.ApplyResources(this.label40, "label40");
            this.label40.Name = "label40";
            // 
            // cbDrmSwich
            // 
            resources.ApplyResources(this.cbDrmSwich, "cbDrmSwich");
            this.cbDrmSwich.Name = "cbDrmSwich";
            this.cbDrmSwich.UseVisualStyleBackColor = true;
            // 
            // grpbQ
            // 
            resources.ApplyResources(this.grpbQ, "grpbQ");
            this.grpbQ.Controls.Add(this.btSetQValue);
            this.grpbQ.Controls.Add(this.btGetQValue);
            this.grpbQ.Controls.Add(this.groupBox34);
            this.grpbQ.Controls.Add(this.groupBox33);
            this.grpbQ.Name = "grpbQ";
            this.grpbQ.TabStop = false;
            // 
            // btSetQValue
            // 
            resources.ApplyResources(this.btSetQValue, "btSetQValue");
            this.btSetQValue.Name = "btSetQValue";
            this.btSetQValue.UseVisualStyleBackColor = true;
            this.btSetQValue.Click += new System.EventHandler(this.btSetQValue_Click);
            // 
            // btGetQValue
            // 
            resources.ApplyResources(this.btGetQValue, "btGetQValue");
            this.btGetQValue.Name = "btGetQValue";
            this.btGetQValue.UseVisualStyleBackColor = true;
            this.btGetQValue.Click += new System.EventHandler(this.btGetQValue_Click);
            // 
            // groupBox34
            // 
            resources.ApplyResources(this.groupBox34, "groupBox34");
            this.groupBox34.Controls.Add(this.tbMaxQSince);
            this.groupBox34.Controls.Add(this.tbNumMinQ);
            this.groupBox34.Controls.Add(this.label45);
            this.groupBox34.Controls.Add(this.label44);
            this.groupBox34.Controls.Add(this.cbbMaxQValue);
            this.groupBox34.Controls.Add(this.label43);
            this.groupBox34.Controls.Add(this.cbbMinQValue);
            this.groupBox34.Controls.Add(this.label42);
            this.groupBox34.Controls.Add(this.cbbInitQValue);
            this.groupBox34.Controls.Add(this.label41);
            this.groupBox34.Name = "groupBox34";
            this.groupBox34.TabStop = false;
            // 
            // tbMaxQSince
            // 
            resources.ApplyResources(this.tbMaxQSince, "tbMaxQSince");
            this.tbMaxQSince.Name = "tbMaxQSince";
            // 
            // tbNumMinQ
            // 
            resources.ApplyResources(this.tbNumMinQ, "tbNumMinQ");
            this.tbNumMinQ.Name = "tbNumMinQ";
            // 
            // label45
            // 
            resources.ApplyResources(this.label45, "label45");
            this.label45.Name = "label45";
            // 
            // label44
            // 
            resources.ApplyResources(this.label44, "label44");
            this.label44.Name = "label44";
            // 
            // cbbMaxQValue
            // 
            resources.ApplyResources(this.cbbMaxQValue, "cbbMaxQValue");
            this.cbbMaxQValue.FormattingEnabled = true;
            this.cbbMaxQValue.Items.AddRange(new object[] {
            resources.GetString("cbbMaxQValue.Items"),
            resources.GetString("cbbMaxQValue.Items1"),
            resources.GetString("cbbMaxQValue.Items2"),
            resources.GetString("cbbMaxQValue.Items3"),
            resources.GetString("cbbMaxQValue.Items4"),
            resources.GetString("cbbMaxQValue.Items5"),
            resources.GetString("cbbMaxQValue.Items6"),
            resources.GetString("cbbMaxQValue.Items7"),
            resources.GetString("cbbMaxQValue.Items8"),
            resources.GetString("cbbMaxQValue.Items9"),
            resources.GetString("cbbMaxQValue.Items10"),
            resources.GetString("cbbMaxQValue.Items11"),
            resources.GetString("cbbMaxQValue.Items12"),
            resources.GetString("cbbMaxQValue.Items13"),
            resources.GetString("cbbMaxQValue.Items14"),
            resources.GetString("cbbMaxQValue.Items15")});
            this.cbbMaxQValue.Name = "cbbMaxQValue";
            // 
            // label43
            // 
            resources.ApplyResources(this.label43, "label43");
            this.label43.Name = "label43";
            // 
            // cbbMinQValue
            // 
            resources.ApplyResources(this.cbbMinQValue, "cbbMinQValue");
            this.cbbMinQValue.FormattingEnabled = true;
            this.cbbMinQValue.Items.AddRange(new object[] {
            resources.GetString("cbbMinQValue.Items"),
            resources.GetString("cbbMinQValue.Items1"),
            resources.GetString("cbbMinQValue.Items2"),
            resources.GetString("cbbMinQValue.Items3"),
            resources.GetString("cbbMinQValue.Items4"),
            resources.GetString("cbbMinQValue.Items5"),
            resources.GetString("cbbMinQValue.Items6"),
            resources.GetString("cbbMinQValue.Items7"),
            resources.GetString("cbbMinQValue.Items8"),
            resources.GetString("cbbMinQValue.Items9"),
            resources.GetString("cbbMinQValue.Items10"),
            resources.GetString("cbbMinQValue.Items11"),
            resources.GetString("cbbMinQValue.Items12"),
            resources.GetString("cbbMinQValue.Items13"),
            resources.GetString("cbbMinQValue.Items14"),
            resources.GetString("cbbMinQValue.Items15")});
            this.cbbMinQValue.Name = "cbbMinQValue";
            // 
            // label42
            // 
            resources.ApplyResources(this.label42, "label42");
            this.label42.Name = "label42";
            // 
            // cbbInitQValue
            // 
            resources.ApplyResources(this.cbbInitQValue, "cbbInitQValue");
            this.cbbInitQValue.FormattingEnabled = true;
            this.cbbInitQValue.Items.AddRange(new object[] {
            resources.GetString("cbbInitQValue.Items"),
            resources.GetString("cbbInitQValue.Items1"),
            resources.GetString("cbbInitQValue.Items2"),
            resources.GetString("cbbInitQValue.Items3"),
            resources.GetString("cbbInitQValue.Items4"),
            resources.GetString("cbbInitQValue.Items5"),
            resources.GetString("cbbInitQValue.Items6"),
            resources.GetString("cbbInitQValue.Items7"),
            resources.GetString("cbbInitQValue.Items8"),
            resources.GetString("cbbInitQValue.Items9"),
            resources.GetString("cbbInitQValue.Items10"),
            resources.GetString("cbbInitQValue.Items11"),
            resources.GetString("cbbInitQValue.Items12"),
            resources.GetString("cbbInitQValue.Items13"),
            resources.GetString("cbbInitQValue.Items14"),
            resources.GetString("cbbInitQValue.Items15")});
            this.cbbInitQValue.Name = "cbbInitQValue";
            // 
            // label41
            // 
            resources.ApplyResources(this.label41, "label41");
            this.label41.Name = "label41";
            // 
            // groupBox33
            // 
            resources.ApplyResources(this.groupBox33, "groupBox33");
            this.groupBox33.Controls.Add(this.rbStQ);
            this.groupBox33.Controls.Add(this.rbDyQ);
            this.groupBox33.Name = "groupBox33";
            this.groupBox33.TabStop = false;
            // 
            // rbStQ
            // 
            resources.ApplyResources(this.rbStQ, "rbStQ");
            this.rbStQ.Name = "rbStQ";
            this.rbStQ.TabStop = true;
            this.rbStQ.UseVisualStyleBackColor = true;
            this.rbStQ.CheckedChanged += new System.EventHandler(this.QType_CheckedChanged);
            // 
            // rbDyQ
            // 
            resources.ApplyResources(this.rbDyQ, "rbDyQ");
            this.rbDyQ.Name = "rbDyQ";
            this.rbDyQ.TabStop = true;
            this.rbDyQ.UseVisualStyleBackColor = true;
            this.rbDyQ.CheckedChanged += new System.EventHandler(this.QType_CheckedChanged);
            // 
            // groupBox32
            // 
            resources.ApplyResources(this.groupBox32, "groupBox32");
            this.groupBox32.Controls.Add(this.groupBox36);
            this.groupBox32.Controls.Add(this.groupBox35);
            this.groupBox32.Name = "groupBox32";
            this.groupBox32.TabStop = false;
            // 
            // groupBox36
            // 
            resources.ApplyResources(this.groupBox36, "groupBox36");
            this.groupBox36.Controls.Add(this.groupBox38);
            this.groupBox36.Controls.Add(this.groupBox37);
            this.groupBox36.Name = "groupBox36";
            this.groupBox36.TabStop = false;
            // 
            // groupBox38
            // 
            resources.ApplyResources(this.groupBox38, "groupBox38");
            this.groupBox38.Controls.Add(this.label95);
            this.groupBox38.Controls.Add(this.lbModelSendCnt);
            this.groupBox38.Controls.Add(this.lbModelTestTimeCnt);
            this.groupBox38.Controls.Add(this.label85);
            this.groupBox38.Controls.Add(this.label97);
            this.groupBox38.Controls.Add(this.label74);
            this.groupBox38.Controls.Add(this.lbModelRevCnt);
            this.groupBox38.Name = "groupBox38";
            this.groupBox38.TabStop = false;
            // 
            // label95
            // 
            resources.ApplyResources(this.label95, "label95");
            this.label95.Name = "label95";
            // 
            // lbModelSendCnt
            // 
            resources.ApplyResources(this.lbModelSendCnt, "lbModelSendCnt");
            this.lbModelSendCnt.Name = "lbModelSendCnt";
            // 
            // lbModelTestTimeCnt
            // 
            resources.ApplyResources(this.lbModelTestTimeCnt, "lbModelTestTimeCnt");
            this.lbModelTestTimeCnt.Name = "lbModelTestTimeCnt";
            // 
            // label85
            // 
            resources.ApplyResources(this.label85, "label85");
            this.label85.Name = "label85";
            // 
            // label97
            // 
            resources.ApplyResources(this.label97, "label97");
            this.label97.Name = "label97";
            // 
            // label74
            // 
            resources.ApplyResources(this.label74, "label74");
            this.label74.Name = "label74";
            // 
            // lbModelRevCnt
            // 
            resources.ApplyResources(this.lbModelRevCnt, "lbModelRevCnt");
            this.lbModelRevCnt.Name = "lbModelRevCnt";
            // 
            // groupBox37
            // 
            resources.ApplyResources(this.groupBox37, "groupBox37");
            this.groupBox37.Controls.Add(this.label94);
            this.groupBox37.Controls.Add(this.lbPCTestTimeCnt);
            this.groupBox37.Controls.Add(this.label92);
            this.groupBox37.Controls.Add(this.lbPCRecCnt);
            this.groupBox37.Controls.Add(this.label70);
            this.groupBox37.Controls.Add(this.lbPCSendCnt);
            this.groupBox37.Controls.Add(this.label60);
            this.groupBox37.Name = "groupBox37";
            this.groupBox37.TabStop = false;
            // 
            // label94
            // 
            resources.ApplyResources(this.label94, "label94");
            this.label94.Name = "label94";
            // 
            // lbPCTestTimeCnt
            // 
            resources.ApplyResources(this.lbPCTestTimeCnt, "lbPCTestTimeCnt");
            this.lbPCTestTimeCnt.Name = "lbPCTestTimeCnt";
            // 
            // label92
            // 
            resources.ApplyResources(this.label92, "label92");
            this.label92.Name = "label92";
            // 
            // lbPCRecCnt
            // 
            resources.ApplyResources(this.lbPCRecCnt, "lbPCRecCnt");
            this.lbPCRecCnt.Name = "lbPCRecCnt";
            // 
            // label70
            // 
            resources.ApplyResources(this.label70, "label70");
            this.label70.Name = "label70";
            // 
            // lbPCSendCnt
            // 
            resources.ApplyResources(this.lbPCSendCnt, "lbPCSendCnt");
            this.lbPCSendCnt.Name = "lbPCSendCnt";
            // 
            // label60
            // 
            resources.ApplyResources(this.label60, "label60");
            this.label60.Name = "label60";
            // 
            // groupBox35
            // 
            resources.ApplyResources(this.groupBox35, "groupBox35");
            this.groupBox35.Controls.Add(this.label72);
            this.groupBox35.Controls.Add(this.label62);
            this.groupBox35.Controls.Add(this.tbSendPeroid);
            this.groupBox35.Controls.Add(this.cbSendPeroid);
            this.groupBox35.Controls.Add(this.btnSerialTest);
            this.groupBox35.Controls.Add(this.tbTestCmd);
            this.groupBox35.Controls.Add(this.label52);
            this.groupBox35.Controls.Add(this.tbCmdLen);
            this.groupBox35.Controls.Add(this.label51);
            this.groupBox35.Controls.Add(this.tbTestCnt);
            this.groupBox35.Controls.Add(this.label50);
            this.groupBox35.Controls.Add(this.cbbTestModel);
            this.groupBox35.Controls.Add(this.label48);
            this.groupBox35.Name = "groupBox35";
            this.groupBox35.TabStop = false;
            // 
            // label72
            // 
            resources.ApplyResources(this.label72, "label72");
            this.label72.Name = "label72";
            // 
            // label62
            // 
            resources.ApplyResources(this.label62, "label62");
            this.label62.Name = "label62";
            // 
            // tbSendPeroid
            // 
            resources.ApplyResources(this.tbSendPeroid, "tbSendPeroid");
            this.tbSendPeroid.Name = "tbSendPeroid";
            // 
            // cbSendPeroid
            // 
            resources.ApplyResources(this.cbSendPeroid, "cbSendPeroid");
            this.cbSendPeroid.Name = "cbSendPeroid";
            this.cbSendPeroid.UseVisualStyleBackColor = true;
            // 
            // btnSerialTest
            // 
            resources.ApplyResources(this.btnSerialTest, "btnSerialTest");
            this.btnSerialTest.Name = "btnSerialTest";
            this.btnSerialTest.UseVisualStyleBackColor = true;
            this.btnSerialTest.Click += new System.EventHandler(this.btnSerialTest_Click);
            // 
            // tbTestCmd
            // 
            resources.ApplyResources(this.tbTestCmd, "tbTestCmd");
            this.tbTestCmd.Name = "tbTestCmd";
            // 
            // label52
            // 
            resources.ApplyResources(this.label52, "label52");
            this.label52.Name = "label52";
            // 
            // tbCmdLen
            // 
            resources.ApplyResources(this.tbCmdLen, "tbCmdLen");
            this.tbCmdLen.Name = "tbCmdLen";
            // 
            // label51
            // 
            resources.ApplyResources(this.label51, "label51");
            this.label51.Name = "label51";
            // 
            // tbTestCnt
            // 
            resources.ApplyResources(this.tbTestCnt, "tbTestCnt");
            this.tbTestCnt.Name = "tbTestCnt";
            // 
            // label50
            // 
            resources.ApplyResources(this.label50, "label50");
            this.label50.Name = "label50";
            // 
            // cbbTestModel
            // 
            resources.ApplyResources(this.cbbTestModel, "cbbTestModel");
            this.cbbTestModel.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cbbTestModel.FormattingEnabled = true;
            this.cbbTestModel.Items.AddRange(new object[] {
            resources.GetString("cbbTestModel.Items"),
            resources.GetString("cbbTestModel.Items1"),
            resources.GetString("cbbTestModel.Items2"),
            resources.GetString("cbbTestModel.Items3")});
            this.cbbTestModel.Name = "cbbTestModel";
            this.cbbTestModel.SelectedIndexChanged += new System.EventHandler(this.cbbTestModel_SelectedIndexChanged);
            // 
            // label48
            // 
            resources.ApplyResources(this.label48, "label48");
            this.label48.Name = "label48";
            // 
            // tabPage5
            // 
            resources.ApplyResources(this.tabPage5, "tabPage5");
            this.tabPage5.BackColor = System.Drawing.Color.WhiteSmoke;
            this.tabPage5.Controls.Add(this.groupBox29);
            this.tabPage5.Name = "tabPage5";
            // 
            // groupBox29
            // 
            resources.ApplyResources(this.groupBox29, "groupBox29");
            this.groupBox29.Controls.Add(this.btSetTm600Profile);
            this.groupBox29.Controls.Add(this.btGetTm600Profile);
            this.groupBox29.Controls.Add(this.cbbTm600RFLink);
            this.groupBox29.Controls.Add(this.label46);
            this.groupBox29.Name = "groupBox29";
            this.groupBox29.TabStop = false;
            // 
            // btSetTm600Profile
            // 
            resources.ApplyResources(this.btSetTm600Profile, "btSetTm600Profile");
            this.btSetTm600Profile.Name = "btSetTm600Profile";
            this.btSetTm600Profile.UseVisualStyleBackColor = true;
            this.btSetTm600Profile.Click += new System.EventHandler(this.btSetTm600Profile_Click);
            // 
            // btGetTm600Profile
            // 
            resources.ApplyResources(this.btGetTm600Profile, "btGetTm600Profile");
            this.btGetTm600Profile.Name = "btGetTm600Profile";
            this.btGetTm600Profile.UseVisualStyleBackColor = true;
            this.btGetTm600Profile.Click += new System.EventHandler(this.btGetTm600Profile_Click);
            // 
            // cbbTm600RFLink
            // 
            resources.ApplyResources(this.cbbTm600RFLink, "cbbTm600RFLink");
            this.cbbTm600RFLink.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cbbTm600RFLink.FormattingEnabled = true;
            this.cbbTm600RFLink.Items.AddRange(new object[] {
            resources.GetString("cbbTm600RFLink.Items"),
            resources.GetString("cbbTm600RFLink.Items1"),
            resources.GetString("cbbTm600RFLink.Items2"),
            resources.GetString("cbbTm600RFLink.Items3"),
            resources.GetString("cbbTm600RFLink.Items4"),
            resources.GetString("cbbTm600RFLink.Items5"),
            resources.GetString("cbbTm600RFLink.Items6"),
            resources.GetString("cbbTm600RFLink.Items7"),
            resources.GetString("cbbTm600RFLink.Items8"),
            resources.GetString("cbbTm600RFLink.Items9"),
            resources.GetString("cbbTm600RFLink.Items10"),
            resources.GetString("cbbTm600RFLink.Items11"),
            resources.GetString("cbbTm600RFLink.Items12"),
            resources.GetString("cbbTm600RFLink.Items13"),
            resources.GetString("cbbTm600RFLink.Items14"),
            resources.GetString("cbbTm600RFLink.Items15"),
            resources.GetString("cbbTm600RFLink.Items16"),
            resources.GetString("cbbTm600RFLink.Items17"),
            resources.GetString("cbbTm600RFLink.Items18"),
            resources.GetString("cbbTm600RFLink.Items19")});
            this.cbbTm600RFLink.Name = "cbbTm600RFLink";
            // 
            // label46
            // 
            resources.ApplyResources(this.label46, "label46");
            this.label46.Name = "label46";
            // 
            // pageEpcTest
            // 
            resources.ApplyResources(this.pageEpcTest, "pageEpcTest");
            this.pageEpcTest.BackColor = System.Drawing.Color.WhiteSmoke;
            this.pageEpcTest.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.pageEpcTest.Controls.Add(this.tab_6c_Tags_Test);
            this.pageEpcTest.ForeColor = System.Drawing.SystemColors.Desktop;
            this.pageEpcTest.Name = "pageEpcTest";
            // 
            // tab_6c_Tags_Test
            // 
            resources.ApplyResources(this.tab_6c_Tags_Test, "tab_6c_Tags_Test");
            this.tab_6c_Tags_Test.Controls.Add(this.pageFast4AntMode);
            this.tab_6c_Tags_Test.Controls.Add(this.pageAcessTag);
            this.tab_6c_Tags_Test.Name = "tab_6c_Tags_Test";
            this.tab_6c_Tags_Test.SelectedIndex = 0;
            this.tab_6c_Tags_Test.TabStop = false;
            // 
            // pageFast4AntMode
            // 
            resources.ApplyResources(this.pageFast4AntMode, "pageFast4AntMode");
            this.pageFast4AntMode.BackColor = System.Drawing.Color.WhiteSmoke;
            this.pageFast4AntMode.Controls.Add(this.panel2);
            this.pageFast4AntMode.Controls.Add(this.panel14);
            this.pageFast4AntMode.Controls.Add(this.groupBox26);
            this.pageFast4AntMode.Controls.Add(this.groupBox25);
            this.pageFast4AntMode.Controls.Add(this.groupBox2);
            this.pageFast4AntMode.ForeColor = System.Drawing.SystemColors.Desktop;
            this.pageFast4AntMode.Name = "pageFast4AntMode";
            // 
            // panel2
            // 
            resources.ApplyResources(this.panel2, "panel2");
            this.panel2.Controls.Add(this.lLbTagFilter);
            this.panel2.Controls.Add(this.flowLayoutPanel1);
            this.panel2.Controls.Add(this.flowLayoutPanel5);
            this.panel2.Controls.Add(this.lLbConfig);
            this.panel2.Name = "panel2";
            // 
            // lLbTagFilter
            // 
            resources.ApplyResources(this.lLbTagFilter, "lLbTagFilter");
            this.lLbTagFilter.Name = "lLbTagFilter";
            this.lLbTagFilter.TabStop = true;
            this.lLbTagFilter.LinkClicked += new System.Windows.Forms.LinkLabelLinkClickedEventHandler(this.lLbTagFilter_LinkClicked);
            // 
            // flowLayoutPanel1
            // 
            resources.ApplyResources(this.flowLayoutPanel1, "flowLayoutPanel1");
            this.flowLayoutPanel1.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.flowLayoutPanel1.Controls.Add(this.grb_inventory_cfg);
            this.flowLayoutPanel1.Controls.Add(this.grb_Interval);
            this.flowLayoutPanel1.Controls.Add(this.grb_Reserve);
            this.flowLayoutPanel1.Controls.Add(this.grb_selectFlags);
            this.flowLayoutPanel1.Controls.Add(this.grb_sessions);
            this.flowLayoutPanel1.Controls.Add(this.grb_targets);
            this.flowLayoutPanel1.Controls.Add(this.grb_Optimize);
            this.flowLayoutPanel1.Controls.Add(this.grb_Ongoing);
            this.flowLayoutPanel1.Controls.Add(this.grb_TargetQuantity);
            this.flowLayoutPanel1.Controls.Add(this.grb_powerSave);
            this.flowLayoutPanel1.Controls.Add(this.grb_Repeat);
            this.flowLayoutPanel1.Controls.Add(this.grb_multi_ant);
            this.flowLayoutPanel1.Controls.Add(this.grb_ants_g1);
            this.flowLayoutPanel1.Controls.Add(this.grb_temp_pow_ants_g1);
            this.flowLayoutPanel1.Controls.Add(this.grb_ants_g2);
            this.flowLayoutPanel1.Controls.Add(this.grb_temp_pow_ants_g2);
            this.flowLayoutPanel1.Controls.Add(this.grb_real_inv_ants);
            this.flowLayoutPanel1.Name = "flowLayoutPanel1";
            // 
            // grb_inventory_cfg
            // 
            resources.ApplyResources(this.grb_inventory_cfg, "grb_inventory_cfg");
            this.grb_inventory_cfg.Controls.Add(this.cb_use_selectFlags_tempPows);
            this.grb_inventory_cfg.Controls.Add(this.cb_use_optimize);
            this.grb_inventory_cfg.Controls.Add(this.cb_use_Phase);
            this.grb_inventory_cfg.Controls.Add(this.cb_use_powerSave);
            this.grb_inventory_cfg.Controls.Add(this.cb_customized_session_target);
            this.grb_inventory_cfg.Name = "grb_inventory_cfg";
            this.grb_inventory_cfg.TabStop = false;
            // 
            // cb_use_selectFlags_tempPows
            // 
            resources.ApplyResources(this.cb_use_selectFlags_tempPows, "cb_use_selectFlags_tempPows");
            this.cb_use_selectFlags_tempPows.Name = "cb_use_selectFlags_tempPows";
            this.cb_use_selectFlags_tempPows.UseVisualStyleBackColor = true;
            this.cb_use_selectFlags_tempPows.CheckedChanged += new System.EventHandler(this.cb_use_selectFlags_tempPows_CheckedChanged);
            // 
            // cb_use_optimize
            // 
            resources.ApplyResources(this.cb_use_optimize, "cb_use_optimize");
            this.cb_use_optimize.Name = "cb_use_optimize";
            this.cb_use_optimize.UseVisualStyleBackColor = true;
            this.cb_use_optimize.CheckedChanged += new System.EventHandler(this.cb_use_optimize_CheckedChanged);
            // 
            // cb_use_Phase
            // 
            resources.ApplyResources(this.cb_use_Phase, "cb_use_Phase");
            this.cb_use_Phase.Name = "cb_use_Phase";
            this.cb_use_Phase.UseVisualStyleBackColor = true;
            this.cb_use_Phase.CheckedChanged += new System.EventHandler(this.cb_use_Phase_CheckedChanged);
            // 
            // cb_use_powerSave
            // 
            resources.ApplyResources(this.cb_use_powerSave, "cb_use_powerSave");
            this.cb_use_powerSave.Name = "cb_use_powerSave";
            this.cb_use_powerSave.UseVisualStyleBackColor = true;
            this.cb_use_powerSave.CheckedChanged += new System.EventHandler(this.cb_use_powerSave_CheckedChanged);
            // 
            // cb_customized_session_target
            // 
            resources.ApplyResources(this.cb_customized_session_target, "cb_customized_session_target");
            this.cb_customized_session_target.Name = "cb_customized_session_target";
            this.cb_customized_session_target.UseVisualStyleBackColor = true;
            this.cb_customized_session_target.CheckedChanged += new System.EventHandler(this.cb_customized_session_target_CheckedChanged);
            // 
            // grb_Interval
            // 
            resources.ApplyResources(this.grb_Interval, "grb_Interval");
            this.grb_Interval.Controls.Add(this.txtInterval);
            this.grb_Interval.Name = "grb_Interval";
            this.grb_Interval.TabStop = false;
            // 
            // txtInterval
            // 
            resources.ApplyResources(this.txtInterval, "txtInterval");
            this.txtInterval.Name = "txtInterval";
            this.txtInterval.TextChanged += new System.EventHandler(this.txtInterval_TextChanged);
            // 
            // grb_Reserve
            // 
            resources.ApplyResources(this.grb_Reserve, "grb_Reserve");
            this.grb_Reserve.Controls.Add(this.tb_fast_inv_reserved_1);
            this.grb_Reserve.Controls.Add(this.tb_fast_inv_reserved_3);
            this.grb_Reserve.Controls.Add(this.tb_fast_inv_reserved_4);
            this.grb_Reserve.Controls.Add(this.tb_fast_inv_reserved_2);
            this.grb_Reserve.Controls.Add(this.tb_fast_inv_reserved_5);
            this.grb_Reserve.Name = "grb_Reserve";
            this.grb_Reserve.TabStop = false;
            // 
            // tb_fast_inv_reserved_1
            // 
            resources.ApplyResources(this.tb_fast_inv_reserved_1, "tb_fast_inv_reserved_1");
            this.tb_fast_inv_reserved_1.Name = "tb_fast_inv_reserved_1";
            this.tb_fast_inv_reserved_1.TextChanged += new System.EventHandler(this.tb_fast_inv_reserved_1_TextChanged);
            // 
            // tb_fast_inv_reserved_3
            // 
            resources.ApplyResources(this.tb_fast_inv_reserved_3, "tb_fast_inv_reserved_3");
            this.tb_fast_inv_reserved_3.Name = "tb_fast_inv_reserved_3";
            this.tb_fast_inv_reserved_3.TextChanged += new System.EventHandler(this.tb_fast_inv_reserved_3_TextChanged);
            // 
            // tb_fast_inv_reserved_4
            // 
            resources.ApplyResources(this.tb_fast_inv_reserved_4, "tb_fast_inv_reserved_4");
            this.tb_fast_inv_reserved_4.Name = "tb_fast_inv_reserved_4";
            this.tb_fast_inv_reserved_4.TextChanged += new System.EventHandler(this.tb_fast_inv_reserved_4_TextChanged);
            // 
            // tb_fast_inv_reserved_2
            // 
            resources.ApplyResources(this.tb_fast_inv_reserved_2, "tb_fast_inv_reserved_2");
            this.tb_fast_inv_reserved_2.Name = "tb_fast_inv_reserved_2";
            this.tb_fast_inv_reserved_2.TextChanged += new System.EventHandler(this.tb_fast_inv_reserved_2_TextChanged);
            // 
            // tb_fast_inv_reserved_5
            // 
            resources.ApplyResources(this.tb_fast_inv_reserved_5, "tb_fast_inv_reserved_5");
            this.tb_fast_inv_reserved_5.Name = "tb_fast_inv_reserved_5";
            this.tb_fast_inv_reserved_5.TextChanged += new System.EventHandler(this.tb_fast_inv_reserved_5_TextChanged);
            // 
            // grb_selectFlags
            // 
            resources.ApplyResources(this.grb_selectFlags, "grb_selectFlags");
            this.grb_selectFlags.Controls.Add(this.radio_btn_sl_03);
            this.grb_selectFlags.Controls.Add(this.radio_btn_sl_02);
            this.grb_selectFlags.Controls.Add(this.radio_btn_sl_01);
            this.grb_selectFlags.Controls.Add(this.radio_btn_sl_00);
            this.grb_selectFlags.Name = "grb_selectFlags";
            this.grb_selectFlags.TabStop = false;
            // 
            // radio_btn_sl_03
            // 
            resources.ApplyResources(this.radio_btn_sl_03, "radio_btn_sl_03");
            this.radio_btn_sl_03.Name = "radio_btn_sl_03";
            this.radio_btn_sl_03.TabStop = true;
            this.radio_btn_sl_03.UseVisualStyleBackColor = true;
            // 
            // radio_btn_sl_02
            // 
            resources.ApplyResources(this.radio_btn_sl_02, "radio_btn_sl_02");
            this.radio_btn_sl_02.Name = "radio_btn_sl_02";
            this.radio_btn_sl_02.TabStop = true;
            this.radio_btn_sl_02.UseVisualStyleBackColor = true;
            // 
            // radio_btn_sl_01
            // 
            resources.ApplyResources(this.radio_btn_sl_01, "radio_btn_sl_01");
            this.radio_btn_sl_01.Name = "radio_btn_sl_01";
            this.radio_btn_sl_01.TabStop = true;
            this.radio_btn_sl_01.UseVisualStyleBackColor = true;
            // 
            // radio_btn_sl_00
            // 
            resources.ApplyResources(this.radio_btn_sl_00, "radio_btn_sl_00");
            this.radio_btn_sl_00.Name = "radio_btn_sl_00";
            this.radio_btn_sl_00.TabStop = true;
            this.radio_btn_sl_00.UseVisualStyleBackColor = true;
            // 
            // grb_sessions
            // 
            resources.ApplyResources(this.grb_sessions, "grb_sessions");
            this.grb_sessions.Controls.Add(this.radio_btn_S0);
            this.grb_sessions.Controls.Add(this.radio_btn_S1);
            this.grb_sessions.Controls.Add(this.radio_btn_S2);
            this.grb_sessions.Controls.Add(this.radio_btn_S3);
            this.grb_sessions.Name = "grb_sessions";
            this.grb_sessions.TabStop = false;
            // 
            // radio_btn_S0
            // 
            resources.ApplyResources(this.radio_btn_S0, "radio_btn_S0");
            this.radio_btn_S0.Name = "radio_btn_S0";
            this.radio_btn_S0.TabStop = true;
            this.radio_btn_S0.UseVisualStyleBackColor = true;
            // 
            // radio_btn_S1
            // 
            resources.ApplyResources(this.radio_btn_S1, "radio_btn_S1");
            this.radio_btn_S1.Name = "radio_btn_S1";
            this.radio_btn_S1.TabStop = true;
            this.radio_btn_S1.UseVisualStyleBackColor = true;
            // 
            // radio_btn_S2
            // 
            resources.ApplyResources(this.radio_btn_S2, "radio_btn_S2");
            this.radio_btn_S2.Name = "radio_btn_S2";
            this.radio_btn_S2.TabStop = true;
            this.radio_btn_S2.UseVisualStyleBackColor = true;
            // 
            // radio_btn_S3
            // 
            resources.ApplyResources(this.radio_btn_S3, "radio_btn_S3");
            this.radio_btn_S3.Name = "radio_btn_S3";
            this.radio_btn_S3.TabStop = true;
            this.radio_btn_S3.UseVisualStyleBackColor = true;
            // 
            // grb_targets
            // 
            resources.ApplyResources(this.grb_targets, "grb_targets");
            this.grb_targets.Controls.Add(this.radio_btn_target_A);
            this.grb_targets.Controls.Add(this.radio_btn_target_B);
            this.grb_targets.Name = "grb_targets";
            this.grb_targets.TabStop = false;
            // 
            // radio_btn_target_A
            // 
            resources.ApplyResources(this.radio_btn_target_A, "radio_btn_target_A");
            this.radio_btn_target_A.Name = "radio_btn_target_A";
            this.radio_btn_target_A.TabStop = true;
            this.radio_btn_target_A.UseVisualStyleBackColor = true;
            // 
            // radio_btn_target_B
            // 
            resources.ApplyResources(this.radio_btn_target_B, "radio_btn_target_B");
            this.radio_btn_target_B.Name = "radio_btn_target_B";
            this.radio_btn_target_B.TabStop = true;
            this.radio_btn_target_B.UseVisualStyleBackColor = true;
            // 
            // grb_Optimize
            // 
            resources.ApplyResources(this.grb_Optimize, "grb_Optimize");
            this.grb_Optimize.Controls.Add(this.txtOptimize);
            this.grb_Optimize.Name = "grb_Optimize";
            this.grb_Optimize.TabStop = false;
            // 
            // txtOptimize
            // 
            resources.ApplyResources(this.txtOptimize, "txtOptimize");
            this.txtOptimize.Name = "txtOptimize";
            this.txtOptimize.TextChanged += new System.EventHandler(this.txtOptimize_TextChanged);
            // 
            // grb_Ongoing
            // 
            resources.ApplyResources(this.grb_Ongoing, "grb_Ongoing");
            this.grb_Ongoing.Controls.Add(this.txtOngoing);
            this.grb_Ongoing.Name = "grb_Ongoing";
            this.grb_Ongoing.TabStop = false;
            // 
            // txtOngoing
            // 
            resources.ApplyResources(this.txtOngoing, "txtOngoing");
            this.txtOngoing.Name = "txtOngoing";
            this.txtOngoing.TextChanged += new System.EventHandler(this.txtOngoing_TextChanged);
            // 
            // grb_TargetQuantity
            // 
            resources.ApplyResources(this.grb_TargetQuantity, "grb_TargetQuantity");
            this.grb_TargetQuantity.Controls.Add(this.txtTargetQuantity);
            this.grb_TargetQuantity.Name = "grb_TargetQuantity";
            this.grb_TargetQuantity.TabStop = false;
            // 
            // txtTargetQuantity
            // 
            resources.ApplyResources(this.txtTargetQuantity, "txtTargetQuantity");
            this.txtTargetQuantity.Name = "txtTargetQuantity";
            this.txtTargetQuantity.TextChanged += new System.EventHandler(this.txtTargetQuantity_TextChanged);
            // 
            // grb_powerSave
            // 
            resources.ApplyResources(this.grb_powerSave, "grb_powerSave");
            this.grb_powerSave.Controls.Add(this.txtPowerSave);
            this.grb_powerSave.Name = "grb_powerSave";
            this.grb_powerSave.TabStop = false;
            // 
            // txtPowerSave
            // 
            resources.ApplyResources(this.txtPowerSave, "txtPowerSave");
            this.txtPowerSave.Name = "txtPowerSave";
            this.txtPowerSave.TextChanged += new System.EventHandler(this.txtPowerSave_TextChanged);
            // 
            // grb_Repeat
            // 
            resources.ApplyResources(this.grb_Repeat, "grb_Repeat");
            this.grb_Repeat.Controls.Add(this.txtRepeat);
            this.grb_Repeat.Name = "grb_Repeat";
            this.grb_Repeat.TabStop = false;
            // 
            // txtRepeat
            // 
            resources.ApplyResources(this.txtRepeat, "txtRepeat");
            this.txtRepeat.Name = "txtRepeat";
            this.txtRepeat.TextChanged += new System.EventHandler(this.txtRepeat_TextChanged);
            // 
            // grb_multi_ant
            // 
            resources.ApplyResources(this.grb_multi_ant, "grb_multi_ant");
            this.grb_multi_ant.Controls.Add(this.cb_fast_inv_check_all_ant);
            this.grb_multi_ant.Name = "grb_multi_ant";
            this.grb_multi_ant.TabStop = false;
            // 
            // cb_fast_inv_check_all_ant
            // 
            resources.ApplyResources(this.cb_fast_inv_check_all_ant, "cb_fast_inv_check_all_ant");
            this.cb_fast_inv_check_all_ant.Name = "cb_fast_inv_check_all_ant";
            this.cb_fast_inv_check_all_ant.UseVisualStyleBackColor = true;
            this.cb_fast_inv_check_all_ant.CheckedChanged += new System.EventHandler(this.cb_fast_inv_check_all_ant_CheckedChanged);
            // 
            // grb_ants_g1
            // 
            resources.ApplyResources(this.grb_ants_g1, "grb_ants_g1");
            this.grb_ants_g1.Controls.Add(this.chckbx_fast_inv_ant_5);
            this.grb_ants_g1.Controls.Add(this.chckbx_fast_inv_ant_6);
            this.grb_ants_g1.Controls.Add(this.chckbx_fast_inv_ant_1);
            this.grb_ants_g1.Controls.Add(this.txt_fast_inv_Stay_6);
            this.grb_ants_g1.Controls.Add(this.chckbx_fast_inv_ant_4);
            this.grb_ants_g1.Controls.Add(this.chckbx_fast_inv_ant_8);
            this.grb_ants_g1.Controls.Add(this.txt_fast_inv_Stay_1);
            this.grb_ants_g1.Controls.Add(this.txt_fast_inv_Stay_7);
            this.grb_ants_g1.Controls.Add(this.txt_fast_inv_Stay_2);
            this.grb_ants_g1.Controls.Add(this.txt_fast_inv_Stay_5);
            this.grb_ants_g1.Controls.Add(this.txt_fast_inv_Stay_3);
            this.grb_ants_g1.Controls.Add(this.chckbx_fast_inv_ant_7);
            this.grb_ants_g1.Controls.Add(this.chckbx_fast_inv_ant_3);
            this.grb_ants_g1.Controls.Add(this.txt_fast_inv_Stay_8);
            this.grb_ants_g1.Controls.Add(this.txt_fast_inv_Stay_4);
            this.grb_ants_g1.Controls.Add(this.chckbx_fast_inv_ant_2);
            this.grb_ants_g1.Name = "grb_ants_g1";
            this.grb_ants_g1.TabStop = false;
            // 
            // chckbx_fast_inv_ant_5
            // 
            resources.ApplyResources(this.chckbx_fast_inv_ant_5, "chckbx_fast_inv_ant_5");
            this.chckbx_fast_inv_ant_5.Name = "chckbx_fast_inv_ant_5";
            this.chckbx_fast_inv_ant_5.UseVisualStyleBackColor = true;
            // 
            // chckbx_fast_inv_ant_6
            // 
            resources.ApplyResources(this.chckbx_fast_inv_ant_6, "chckbx_fast_inv_ant_6");
            this.chckbx_fast_inv_ant_6.Name = "chckbx_fast_inv_ant_6";
            this.chckbx_fast_inv_ant_6.UseVisualStyleBackColor = true;
            // 
            // chckbx_fast_inv_ant_1
            // 
            resources.ApplyResources(this.chckbx_fast_inv_ant_1, "chckbx_fast_inv_ant_1");
            this.chckbx_fast_inv_ant_1.Name = "chckbx_fast_inv_ant_1";
            this.chckbx_fast_inv_ant_1.UseVisualStyleBackColor = true;
            // 
            // txt_fast_inv_Stay_6
            // 
            resources.ApplyResources(this.txt_fast_inv_Stay_6, "txt_fast_inv_Stay_6");
            this.txt_fast_inv_Stay_6.Name = "txt_fast_inv_Stay_6";
            // 
            // chckbx_fast_inv_ant_4
            // 
            resources.ApplyResources(this.chckbx_fast_inv_ant_4, "chckbx_fast_inv_ant_4");
            this.chckbx_fast_inv_ant_4.Name = "chckbx_fast_inv_ant_4";
            this.chckbx_fast_inv_ant_4.UseVisualStyleBackColor = true;
            // 
            // chckbx_fast_inv_ant_8
            // 
            resources.ApplyResources(this.chckbx_fast_inv_ant_8, "chckbx_fast_inv_ant_8");
            this.chckbx_fast_inv_ant_8.Name = "chckbx_fast_inv_ant_8";
            this.chckbx_fast_inv_ant_8.UseVisualStyleBackColor = true;
            // 
            // txt_fast_inv_Stay_1
            // 
            resources.ApplyResources(this.txt_fast_inv_Stay_1, "txt_fast_inv_Stay_1");
            this.txt_fast_inv_Stay_1.Name = "txt_fast_inv_Stay_1";
            // 
            // txt_fast_inv_Stay_7
            // 
            resources.ApplyResources(this.txt_fast_inv_Stay_7, "txt_fast_inv_Stay_7");
            this.txt_fast_inv_Stay_7.Name = "txt_fast_inv_Stay_7";
            // 
            // txt_fast_inv_Stay_2
            // 
            resources.ApplyResources(this.txt_fast_inv_Stay_2, "txt_fast_inv_Stay_2");
            this.txt_fast_inv_Stay_2.Name = "txt_fast_inv_Stay_2";
            // 
            // txt_fast_inv_Stay_5
            // 
            resources.ApplyResources(this.txt_fast_inv_Stay_5, "txt_fast_inv_Stay_5");
            this.txt_fast_inv_Stay_5.Name = "txt_fast_inv_Stay_5";
            // 
            // txt_fast_inv_Stay_3
            // 
            resources.ApplyResources(this.txt_fast_inv_Stay_3, "txt_fast_inv_Stay_3");
            this.txt_fast_inv_Stay_3.Name = "txt_fast_inv_Stay_3";
            // 
            // chckbx_fast_inv_ant_7
            // 
            resources.ApplyResources(this.chckbx_fast_inv_ant_7, "chckbx_fast_inv_ant_7");
            this.chckbx_fast_inv_ant_7.Name = "chckbx_fast_inv_ant_7";
            this.chckbx_fast_inv_ant_7.UseVisualStyleBackColor = true;
            // 
            // chckbx_fast_inv_ant_3
            // 
            resources.ApplyResources(this.chckbx_fast_inv_ant_3, "chckbx_fast_inv_ant_3");
            this.chckbx_fast_inv_ant_3.Name = "chckbx_fast_inv_ant_3";
            this.chckbx_fast_inv_ant_3.UseVisualStyleBackColor = true;
            // 
            // txt_fast_inv_Stay_8
            // 
            resources.ApplyResources(this.txt_fast_inv_Stay_8, "txt_fast_inv_Stay_8");
            this.txt_fast_inv_Stay_8.Name = "txt_fast_inv_Stay_8";
            // 
            // txt_fast_inv_Stay_4
            // 
            resources.ApplyResources(this.txt_fast_inv_Stay_4, "txt_fast_inv_Stay_4");
            this.txt_fast_inv_Stay_4.Name = "txt_fast_inv_Stay_4";
            // 
            // chckbx_fast_inv_ant_2
            // 
            resources.ApplyResources(this.chckbx_fast_inv_ant_2, "chckbx_fast_inv_ant_2");
            this.chckbx_fast_inv_ant_2.Name = "chckbx_fast_inv_ant_2";
            this.chckbx_fast_inv_ant_2.UseVisualStyleBackColor = true;
            // 
            // grb_temp_pow_ants_g1
            // 
            resources.ApplyResources(this.grb_temp_pow_ants_g1, "grb_temp_pow_ants_g1");
            this.grb_temp_pow_ants_g1.Controls.Add(this.tv_temp_pow_6);
            this.grb_temp_pow_ants_g1.Controls.Add(this.tv_temp_pow_1);
            this.grb_temp_pow_ants_g1.Controls.Add(this.tv_temp_pow_5);
            this.grb_temp_pow_ants_g1.Controls.Add(this.tv_temp_pow_7);
            this.grb_temp_pow_ants_g1.Controls.Add(this.tv_temp_pow_3);
            this.grb_temp_pow_ants_g1.Controls.Add(this.tv_temp_pow_8);
            this.grb_temp_pow_ants_g1.Controls.Add(this.tv_temp_pow_4);
            this.grb_temp_pow_ants_g1.Controls.Add(this.tv_temp_pow_2);
            this.grb_temp_pow_ants_g1.Name = "grb_temp_pow_ants_g1";
            this.grb_temp_pow_ants_g1.TabStop = false;
            // 
            // tv_temp_pow_6
            // 
            resources.ApplyResources(this.tv_temp_pow_6, "tv_temp_pow_6");
            this.tv_temp_pow_6.Name = "tv_temp_pow_6";
            // 
            // tv_temp_pow_1
            // 
            resources.ApplyResources(this.tv_temp_pow_1, "tv_temp_pow_1");
            this.tv_temp_pow_1.Name = "tv_temp_pow_1";
            // 
            // tv_temp_pow_5
            // 
            resources.ApplyResources(this.tv_temp_pow_5, "tv_temp_pow_5");
            this.tv_temp_pow_5.Name = "tv_temp_pow_5";
            // 
            // tv_temp_pow_7
            // 
            resources.ApplyResources(this.tv_temp_pow_7, "tv_temp_pow_7");
            this.tv_temp_pow_7.Name = "tv_temp_pow_7";
            // 
            // tv_temp_pow_3
            // 
            resources.ApplyResources(this.tv_temp_pow_3, "tv_temp_pow_3");
            this.tv_temp_pow_3.Name = "tv_temp_pow_3";
            // 
            // tv_temp_pow_8
            // 
            resources.ApplyResources(this.tv_temp_pow_8, "tv_temp_pow_8");
            this.tv_temp_pow_8.Name = "tv_temp_pow_8";
            // 
            // tv_temp_pow_4
            // 
            resources.ApplyResources(this.tv_temp_pow_4, "tv_temp_pow_4");
            this.tv_temp_pow_4.Name = "tv_temp_pow_4";
            // 
            // tv_temp_pow_2
            // 
            resources.ApplyResources(this.tv_temp_pow_2, "tv_temp_pow_2");
            this.tv_temp_pow_2.Name = "tv_temp_pow_2";
            // 
            // grb_ants_g2
            // 
            resources.ApplyResources(this.grb_ants_g2, "grb_ants_g2");
            this.grb_ants_g2.Controls.Add(this.chckbx_fast_inv_ant_9);
            this.grb_ants_g2.Controls.Add(this.chckbx_fast_inv_ant_10);
            this.grb_ants_g2.Controls.Add(this.chckbx_fast_inv_ant_11);
            this.grb_ants_g2.Controls.Add(this.chckbx_fast_inv_ant_12);
            this.grb_ants_g2.Controls.Add(this.chckbx_fast_inv_ant_13);
            this.grb_ants_g2.Controls.Add(this.chckbx_fast_inv_ant_14);
            this.grb_ants_g2.Controls.Add(this.chckbx_fast_inv_ant_15);
            this.grb_ants_g2.Controls.Add(this.chckbx_fast_inv_ant_16);
            this.grb_ants_g2.Controls.Add(this.txt_fast_inv_Stay_9);
            this.grb_ants_g2.Controls.Add(this.txt_fast_inv_Stay_10);
            this.grb_ants_g2.Controls.Add(this.txt_fast_inv_Stay_11);
            this.grb_ants_g2.Controls.Add(this.txt_fast_inv_Stay_12);
            this.grb_ants_g2.Controls.Add(this.txt_fast_inv_Stay_13);
            this.grb_ants_g2.Controls.Add(this.txt_fast_inv_Stay_14);
            this.grb_ants_g2.Controls.Add(this.txt_fast_inv_Stay_16);
            this.grb_ants_g2.Controls.Add(this.txt_fast_inv_Stay_15);
            this.grb_ants_g2.Name = "grb_ants_g2";
            this.grb_ants_g2.TabStop = false;
            // 
            // chckbx_fast_inv_ant_9
            // 
            resources.ApplyResources(this.chckbx_fast_inv_ant_9, "chckbx_fast_inv_ant_9");
            this.chckbx_fast_inv_ant_9.Name = "chckbx_fast_inv_ant_9";
            this.chckbx_fast_inv_ant_9.UseVisualStyleBackColor = true;
            // 
            // chckbx_fast_inv_ant_10
            // 
            resources.ApplyResources(this.chckbx_fast_inv_ant_10, "chckbx_fast_inv_ant_10");
            this.chckbx_fast_inv_ant_10.Name = "chckbx_fast_inv_ant_10";
            this.chckbx_fast_inv_ant_10.UseVisualStyleBackColor = true;
            // 
            // chckbx_fast_inv_ant_11
            // 
            resources.ApplyResources(this.chckbx_fast_inv_ant_11, "chckbx_fast_inv_ant_11");
            this.chckbx_fast_inv_ant_11.Name = "chckbx_fast_inv_ant_11";
            this.chckbx_fast_inv_ant_11.UseVisualStyleBackColor = true;
            // 
            // chckbx_fast_inv_ant_12
            // 
            resources.ApplyResources(this.chckbx_fast_inv_ant_12, "chckbx_fast_inv_ant_12");
            this.chckbx_fast_inv_ant_12.Name = "chckbx_fast_inv_ant_12";
            this.chckbx_fast_inv_ant_12.UseVisualStyleBackColor = true;
            // 
            // chckbx_fast_inv_ant_13
            // 
            resources.ApplyResources(this.chckbx_fast_inv_ant_13, "chckbx_fast_inv_ant_13");
            this.chckbx_fast_inv_ant_13.Name = "chckbx_fast_inv_ant_13";
            this.chckbx_fast_inv_ant_13.UseVisualStyleBackColor = true;
            // 
            // chckbx_fast_inv_ant_14
            // 
            resources.ApplyResources(this.chckbx_fast_inv_ant_14, "chckbx_fast_inv_ant_14");
            this.chckbx_fast_inv_ant_14.Name = "chckbx_fast_inv_ant_14";
            this.chckbx_fast_inv_ant_14.UseVisualStyleBackColor = true;
            // 
            // chckbx_fast_inv_ant_15
            // 
            resources.ApplyResources(this.chckbx_fast_inv_ant_15, "chckbx_fast_inv_ant_15");
            this.chckbx_fast_inv_ant_15.Name = "chckbx_fast_inv_ant_15";
            this.chckbx_fast_inv_ant_15.UseVisualStyleBackColor = true;
            // 
            // chckbx_fast_inv_ant_16
            // 
            resources.ApplyResources(this.chckbx_fast_inv_ant_16, "chckbx_fast_inv_ant_16");
            this.chckbx_fast_inv_ant_16.Name = "chckbx_fast_inv_ant_16";
            this.chckbx_fast_inv_ant_16.UseVisualStyleBackColor = true;
            // 
            // txt_fast_inv_Stay_9
            // 
            resources.ApplyResources(this.txt_fast_inv_Stay_9, "txt_fast_inv_Stay_9");
            this.txt_fast_inv_Stay_9.Name = "txt_fast_inv_Stay_9";
            // 
            // txt_fast_inv_Stay_10
            // 
            resources.ApplyResources(this.txt_fast_inv_Stay_10, "txt_fast_inv_Stay_10");
            this.txt_fast_inv_Stay_10.Name = "txt_fast_inv_Stay_10";
            // 
            // txt_fast_inv_Stay_11
            // 
            resources.ApplyResources(this.txt_fast_inv_Stay_11, "txt_fast_inv_Stay_11");
            this.txt_fast_inv_Stay_11.Name = "txt_fast_inv_Stay_11";
            // 
            // txt_fast_inv_Stay_12
            // 
            resources.ApplyResources(this.txt_fast_inv_Stay_12, "txt_fast_inv_Stay_12");
            this.txt_fast_inv_Stay_12.Name = "txt_fast_inv_Stay_12";
            // 
            // txt_fast_inv_Stay_13
            // 
            resources.ApplyResources(this.txt_fast_inv_Stay_13, "txt_fast_inv_Stay_13");
            this.txt_fast_inv_Stay_13.Name = "txt_fast_inv_Stay_13";
            // 
            // txt_fast_inv_Stay_14
            // 
            resources.ApplyResources(this.txt_fast_inv_Stay_14, "txt_fast_inv_Stay_14");
            this.txt_fast_inv_Stay_14.Name = "txt_fast_inv_Stay_14";
            // 
            // txt_fast_inv_Stay_16
            // 
            resources.ApplyResources(this.txt_fast_inv_Stay_16, "txt_fast_inv_Stay_16");
            this.txt_fast_inv_Stay_16.Name = "txt_fast_inv_Stay_16";
            // 
            // txt_fast_inv_Stay_15
            // 
            resources.ApplyResources(this.txt_fast_inv_Stay_15, "txt_fast_inv_Stay_15");
            this.txt_fast_inv_Stay_15.Name = "txt_fast_inv_Stay_15";
            // 
            // grb_temp_pow_ants_g2
            // 
            resources.ApplyResources(this.grb_temp_pow_ants_g2, "grb_temp_pow_ants_g2");
            this.grb_temp_pow_ants_g2.Controls.Add(this.tv_temp_pow_16);
            this.grb_temp_pow_ants_g2.Controls.Add(this.tv_temp_pow_9);
            this.grb_temp_pow_ants_g2.Controls.Add(this.tv_temp_pow_15);
            this.grb_temp_pow_ants_g2.Controls.Add(this.tv_temp_pow_10);
            this.grb_temp_pow_ants_g2.Controls.Add(this.tv_temp_pow_11);
            this.grb_temp_pow_ants_g2.Controls.Add(this.tv_temp_pow_14);
            this.grb_temp_pow_ants_g2.Controls.Add(this.tv_temp_pow_12);
            this.grb_temp_pow_ants_g2.Controls.Add(this.tv_temp_pow_13);
            this.grb_temp_pow_ants_g2.Name = "grb_temp_pow_ants_g2";
            this.grb_temp_pow_ants_g2.TabStop = false;
            // 
            // tv_temp_pow_16
            // 
            resources.ApplyResources(this.tv_temp_pow_16, "tv_temp_pow_16");
            this.tv_temp_pow_16.Name = "tv_temp_pow_16";
            // 
            // tv_temp_pow_9
            // 
            resources.ApplyResources(this.tv_temp_pow_9, "tv_temp_pow_9");
            this.tv_temp_pow_9.Name = "tv_temp_pow_9";
            // 
            // tv_temp_pow_15
            // 
            resources.ApplyResources(this.tv_temp_pow_15, "tv_temp_pow_15");
            this.tv_temp_pow_15.Name = "tv_temp_pow_15";
            // 
            // tv_temp_pow_10
            // 
            resources.ApplyResources(this.tv_temp_pow_10, "tv_temp_pow_10");
            this.tv_temp_pow_10.Name = "tv_temp_pow_10";
            // 
            // tv_temp_pow_11
            // 
            resources.ApplyResources(this.tv_temp_pow_11, "tv_temp_pow_11");
            this.tv_temp_pow_11.Name = "tv_temp_pow_11";
            // 
            // tv_temp_pow_14
            // 
            resources.ApplyResources(this.tv_temp_pow_14, "tv_temp_pow_14");
            this.tv_temp_pow_14.Name = "tv_temp_pow_14";
            // 
            // tv_temp_pow_12
            // 
            resources.ApplyResources(this.tv_temp_pow_12, "tv_temp_pow_12");
            this.tv_temp_pow_12.Name = "tv_temp_pow_12";
            // 
            // tv_temp_pow_13
            // 
            resources.ApplyResources(this.tv_temp_pow_13, "tv_temp_pow_13");
            this.tv_temp_pow_13.Name = "tv_temp_pow_13";
            // 
            // grb_real_inv_ants
            // 
            resources.ApplyResources(this.grb_real_inv_ants, "grb_real_inv_ants");
            this.grb_real_inv_ants.Controls.Add(this.label61);
            this.grb_real_inv_ants.Controls.Add(this.combo_realtime_inv_ants);
            this.grb_real_inv_ants.Name = "grb_real_inv_ants";
            this.grb_real_inv_ants.TabStop = false;
            // 
            // label61
            // 
            resources.ApplyResources(this.label61, "label61");
            this.label61.Name = "label61";
            // 
            // combo_realtime_inv_ants
            // 
            resources.ApplyResources(this.combo_realtime_inv_ants, "combo_realtime_inv_ants");
            this.combo_realtime_inv_ants.FormattingEnabled = true;
            this.combo_realtime_inv_ants.Name = "combo_realtime_inv_ants";
            // 
            // flowLayoutPanel5
            // 
            resources.ApplyResources(this.flowLayoutPanel5, "flowLayoutPanel5");
            this.flowLayoutPanel5.BorderStyle = System.Windows.Forms.BorderStyle.FixedSingle;
            this.flowLayoutPanel5.Controls.Add(this.groupBox9);
            this.flowLayoutPanel5.Controls.Add(this.groupBox12);
            this.flowLayoutPanel5.Controls.Add(this.groupBox22);
            this.flowLayoutPanel5.Name = "flowLayoutPanel5";
            // 
            // groupBox9
            // 
            resources.ApplyResources(this.groupBox9, "groupBox9");
            this.groupBox9.Controls.Add(this.cmbbxSessionId);
            this.groupBox9.Controls.Add(this.bitLen);
            this.groupBox9.Controls.Add(this.startAddr);
            this.groupBox9.Controls.Add(this.hexTextBox_mask);
            this.groupBox9.Controls.Add(this.label38);
            this.groupBox9.Controls.Add(this.combo_mast_id);
            this.groupBox9.Controls.Add(this.label39);
            this.groupBox9.Controls.Add(this.label71);
            this.groupBox9.Controls.Add(this.label99);
            this.groupBox9.Controls.Add(this.label100);
            this.groupBox9.Controls.Add(this.label101);
            this.groupBox9.Controls.Add(this.label102);
            this.groupBox9.Controls.Add(this.combo_menbank);
            this.groupBox9.Controls.Add(this.combo_action);
            this.groupBox9.Controls.Add(this.btnTagSelect);
            this.groupBox9.ForeColor = System.Drawing.Color.Black;
            this.groupBox9.Name = "groupBox9";
            this.groupBox9.TabStop = false;
            // 
            // cmbbxSessionId
            // 
            resources.ApplyResources(this.cmbbxSessionId, "cmbbxSessionId");
            this.cmbbxSessionId.FormattingEnabled = true;
            this.cmbbxSessionId.Name = "cmbbxSessionId";
            // 
            // bitLen
            // 
            resources.ApplyResources(this.bitLen, "bitLen");
            this.bitLen.Name = "bitLen";
            // 
            // startAddr
            // 
            resources.ApplyResources(this.startAddr, "startAddr");
            this.startAddr.Name = "startAddr";
            // 
            // hexTextBox_mask
            // 
            resources.ApplyResources(this.hexTextBox_mask, "hexTextBox_mask");
            this.hexTextBox_mask.Name = "hexTextBox_mask";
            // 
            // label38
            // 
            resources.ApplyResources(this.label38, "label38");
            this.label38.Name = "label38";
            // 
            // combo_mast_id
            // 
            resources.ApplyResources(this.combo_mast_id, "combo_mast_id");
            this.combo_mast_id.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.combo_mast_id.DropDownWidth = 70;
            this.combo_mast_id.FormattingEnabled = true;
            this.combo_mast_id.Items.AddRange(new object[] {
            resources.GetString("combo_mast_id.Items"),
            resources.GetString("combo_mast_id.Items1"),
            resources.GetString("combo_mast_id.Items2"),
            resources.GetString("combo_mast_id.Items3"),
            resources.GetString("combo_mast_id.Items4")});
            this.combo_mast_id.Name = "combo_mast_id";
            // 
            // label39
            // 
            resources.ApplyResources(this.label39, "label39");
            this.label39.Name = "label39";
            // 
            // label71
            // 
            resources.ApplyResources(this.label71, "label71");
            this.label71.Name = "label71";
            // 
            // label99
            // 
            resources.ApplyResources(this.label99, "label99");
            this.label99.Name = "label99";
            // 
            // label100
            // 
            resources.ApplyResources(this.label100, "label100");
            this.label100.Name = "label100";
            // 
            // label101
            // 
            resources.ApplyResources(this.label101, "label101");
            this.label101.Name = "label101";
            // 
            // label102
            // 
            resources.ApplyResources(this.label102, "label102");
            this.label102.Name = "label102";
            // 
            // combo_menbank
            // 
            resources.ApplyResources(this.combo_menbank, "combo_menbank");
            this.combo_menbank.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.combo_menbank.FormattingEnabled = true;
            this.combo_menbank.Items.AddRange(new object[] {
            resources.GetString("combo_menbank.Items"),
            resources.GetString("combo_menbank.Items1"),
            resources.GetString("combo_menbank.Items2"),
            resources.GetString("combo_menbank.Items3")});
            this.combo_menbank.Name = "combo_menbank";
            // 
            // combo_action
            // 
            resources.ApplyResources(this.combo_action, "combo_action");
            this.combo_action.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.combo_action.FormattingEnabled = true;
            this.combo_action.Items.AddRange(new object[] {
            resources.GetString("combo_action.Items"),
            resources.GetString("combo_action.Items1"),
            resources.GetString("combo_action.Items2"),
            resources.GetString("combo_action.Items3"),
            resources.GetString("combo_action.Items4"),
            resources.GetString("combo_action.Items5"),
            resources.GetString("combo_action.Items6"),
            resources.GetString("combo_action.Items7")});
            this.combo_action.Name = "combo_action";
            // 
            // btnTagSelect
            // 
            resources.ApplyResources(this.btnTagSelect, "btnTagSelect");
            this.btnTagSelect.Name = "btnTagSelect";
            this.btnTagSelect.UseVisualStyleBackColor = true;
            this.btnTagSelect.Click += new System.EventHandler(this.btnSetTagMask_Click);
            // 
            // groupBox12
            // 
            resources.ApplyResources(this.groupBox12, "groupBox12");
            this.groupBox12.Controls.Add(this.label111);
            this.groupBox12.Controls.Add(this.combo_mast_id_Clear);
            this.groupBox12.Controls.Add(this.btnClearTagMask);
            this.groupBox12.ForeColor = System.Drawing.Color.Black;
            this.groupBox12.Name = "groupBox12";
            this.groupBox12.TabStop = false;
            // 
            // label111
            // 
            resources.ApplyResources(this.label111, "label111");
            this.label111.Name = "label111";
            // 
            // combo_mast_id_Clear
            // 
            resources.ApplyResources(this.combo_mast_id_Clear, "combo_mast_id_Clear");
            this.combo_mast_id_Clear.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.combo_mast_id_Clear.FormattingEnabled = true;
            this.combo_mast_id_Clear.Items.AddRange(new object[] {
            resources.GetString("combo_mast_id_Clear.Items"),
            resources.GetString("combo_mast_id_Clear.Items1"),
            resources.GetString("combo_mast_id_Clear.Items2"),
            resources.GetString("combo_mast_id_Clear.Items3"),
            resources.GetString("combo_mast_id_Clear.Items4"),
            resources.GetString("combo_mast_id_Clear.Items5")});
            this.combo_mast_id_Clear.Name = "combo_mast_id_Clear";
            // 
            // btnClearTagMask
            // 
            resources.ApplyResources(this.btnClearTagMask, "btnClearTagMask");
            this.btnClearTagMask.Name = "btnClearTagMask";
            this.btnClearTagMask.UseVisualStyleBackColor = true;
            this.btnClearTagMask.Click += new System.EventHandler(this.btnClearTagMask_Click);
            // 
            // groupBox22
            // 
            resources.ApplyResources(this.groupBox22, "groupBox22");
            this.groupBox22.Controls.Add(this.btnGetTagMask);
            this.groupBox22.ForeColor = System.Drawing.Color.Black;
            this.groupBox22.Name = "groupBox22";
            this.groupBox22.TabStop = false;
            // 
            // btnGetTagMask
            // 
            resources.ApplyResources(this.btnGetTagMask, "btnGetTagMask");
            this.btnGetTagMask.Name = "btnGetTagMask";
            this.btnGetTagMask.UseVisualStyleBackColor = true;
            this.btnGetTagMask.Click += new System.EventHandler(this.btnGetTagMask_Click);
            // 
            // lLbConfig
            // 
            resources.ApplyResources(this.lLbConfig, "lLbConfig");
            this.lLbConfig.Name = "lLbConfig";
            this.lLbConfig.TabStop = true;
            this.lLbConfig.LinkClicked += new System.Windows.Forms.LinkLabelLinkClickedEventHandler(this.lLbConfig_LinkClicked);
            // 
            // panel14
            // 
            resources.ApplyResources(this.panel14, "panel14");
            this.panel14.Controls.Add(this.dgvTagMask);
            this.panel14.Name = "panel14";
            // 
            // dgvTagMask
            // 
            resources.ApplyResources(this.dgvTagMask, "dgvTagMask");
            this.dgvTagMask.ColumnHeadersHeightSizeMode = System.Windows.Forms.DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            this.dgvTagMask.Columns.AddRange(new System.Windows.Forms.DataGridViewColumn[] {
            this.tagMask_MaskNoColumn,
            this.tagMask_SessionIdColumn,
            this.tagMask_ActionColumn,
            this.tagMask_MembankColumn,
            this.tagMask_StartAddrColumn,
            this.tagMask_MaskLenColumn,
            this.tagMask_MaskValueColumn,
            this.tagMask_TruncateColumn});
            this.dgvTagMask.Name = "dgvTagMask";
            this.dgvTagMask.RowTemplate.Height = 23;
            // 
            // tagMask_MaskNoColumn
            // 
            resources.ApplyResources(this.tagMask_MaskNoColumn, "tagMask_MaskNoColumn");
            this.tagMask_MaskNoColumn.Name = "tagMask_MaskNoColumn";
            // 
            // tagMask_SessionIdColumn
            // 
            resources.ApplyResources(this.tagMask_SessionIdColumn, "tagMask_SessionIdColumn");
            this.tagMask_SessionIdColumn.Name = "tagMask_SessionIdColumn";
            // 
            // tagMask_ActionColumn
            // 
            resources.ApplyResources(this.tagMask_ActionColumn, "tagMask_ActionColumn");
            this.tagMask_ActionColumn.Name = "tagMask_ActionColumn";
            // 
            // tagMask_MembankColumn
            // 
            resources.ApplyResources(this.tagMask_MembankColumn, "tagMask_MembankColumn");
            this.tagMask_MembankColumn.Name = "tagMask_MembankColumn";
            // 
            // tagMask_StartAddrColumn
            // 
            resources.ApplyResources(this.tagMask_StartAddrColumn, "tagMask_StartAddrColumn");
            this.tagMask_StartAddrColumn.Name = "tagMask_StartAddrColumn";
            // 
            // tagMask_MaskLenColumn
            // 
            resources.ApplyResources(this.tagMask_MaskLenColumn, "tagMask_MaskLenColumn");
            this.tagMask_MaskLenColumn.Name = "tagMask_MaskLenColumn";
            // 
            // tagMask_MaskValueColumn
            // 
            resources.ApplyResources(this.tagMask_MaskValueColumn, "tagMask_MaskValueColumn");
            this.tagMask_MaskValueColumn.Name = "tagMask_MaskValueColumn";
            // 
            // tagMask_TruncateColumn
            // 
            resources.ApplyResources(this.tagMask_TruncateColumn, "tagMask_TruncateColumn");
            this.tagMask_TruncateColumn.Name = "tagMask_TruncateColumn";
            // 
            // groupBox26
            // 
            resources.ApplyResources(this.groupBox26, "groupBox26");
            this.groupBox26.Controls.Add(this.label53);
            this.groupBox26.Controls.Add(this.txtCmdTagCount);
            this.groupBox26.Controls.Add(this.label49);
            this.groupBox26.Controls.Add(this.label22);
            this.groupBox26.Controls.Add(this.dgvInventoryTagResults);
            this.groupBox26.Controls.Add(this.btnFastRefresh);
            this.groupBox26.Controls.Add(this.txtFastMinRssi);
            this.groupBox26.Controls.Add(this.btnSaveTags);
            this.groupBox26.Controls.Add(this.txtFastMaxRssi);
            this.groupBox26.Name = "groupBox26";
            this.groupBox26.TabStop = false;
            // 
            // label53
            // 
            resources.ApplyResources(this.label53, "label53");
            this.label53.ForeColor = System.Drawing.SystemColors.Desktop;
            this.label53.Name = "label53";
            // 
            // txtCmdTagCount
            // 
            resources.ApplyResources(this.txtCmdTagCount, "txtCmdTagCount");
            this.txtCmdTagCount.ForeColor = System.Drawing.SystemColors.Highlight;
            this.txtCmdTagCount.Name = "txtCmdTagCount";
            // 
            // label49
            // 
            resources.ApplyResources(this.label49, "label49");
            this.label49.ForeColor = System.Drawing.SystemColors.ControlText;
            this.label49.Name = "label49";
            // 
            // label22
            // 
            resources.ApplyResources(this.label22, "label22");
            this.label22.ForeColor = System.Drawing.SystemColors.ControlText;
            this.label22.Name = "label22";
            // 
            // dgvInventoryTagResults
            // 
            resources.ApplyResources(this.dgvInventoryTagResults, "dgvInventoryTagResults");
            this.dgvInventoryTagResults.ColumnHeadersHeightSizeMode = System.Windows.Forms.DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            this.dgvInventoryTagResults.Columns.AddRange(new System.Windows.Forms.DataGridViewColumn[] {
            this.SerialNumber_fast_inv,
            this.ReadCount_fast_inv,
            this.PC_fast_inv,
            this.EPC_fast_inv,
            this.Antenna_fast_inv,
            this.Freq_fast_inv,
            this.Rssi_fast_inv,
            this.Phase_fast_inv,
            this.Data_fast_inv});
            this.dgvInventoryTagResults.Name = "dgvInventoryTagResults";
            this.dgvInventoryTagResults.RowTemplate.Height = 23;
            // 
            // SerialNumber_fast_inv
            // 
            resources.ApplyResources(this.SerialNumber_fast_inv, "SerialNumber_fast_inv");
            this.SerialNumber_fast_inv.Name = "SerialNumber_fast_inv";
            // 
            // ReadCount_fast_inv
            // 
            resources.ApplyResources(this.ReadCount_fast_inv, "ReadCount_fast_inv");
            this.ReadCount_fast_inv.Name = "ReadCount_fast_inv";
            // 
            // PC_fast_inv
            // 
            resources.ApplyResources(this.PC_fast_inv, "PC_fast_inv");
            this.PC_fast_inv.Name = "PC_fast_inv";
            // 
            // EPC_fast_inv
            // 
            resources.ApplyResources(this.EPC_fast_inv, "EPC_fast_inv");
            this.EPC_fast_inv.Name = "EPC_fast_inv";
            // 
            // Antenna_fast_inv
            // 
            resources.ApplyResources(this.Antenna_fast_inv, "Antenna_fast_inv");
            this.Antenna_fast_inv.Name = "Antenna_fast_inv";
            // 
            // Freq_fast_inv
            // 
            resources.ApplyResources(this.Freq_fast_inv, "Freq_fast_inv");
            this.Freq_fast_inv.Name = "Freq_fast_inv";
            // 
            // Rssi_fast_inv
            // 
            resources.ApplyResources(this.Rssi_fast_inv, "Rssi_fast_inv");
            this.Rssi_fast_inv.Name = "Rssi_fast_inv";
            // 
            // Phase_fast_inv
            // 
            resources.ApplyResources(this.Phase_fast_inv, "Phase_fast_inv");
            this.Phase_fast_inv.Name = "Phase_fast_inv";
            // 
            // Data_fast_inv
            // 
            resources.ApplyResources(this.Data_fast_inv, "Data_fast_inv");
            this.Data_fast_inv.Name = "Data_fast_inv";
            // 
            // btnFastRefresh
            // 
            resources.ApplyResources(this.btnFastRefresh, "btnFastRefresh");
            this.btnFastRefresh.ForeColor = System.Drawing.SystemColors.Desktop;
            this.btnFastRefresh.Name = "btnFastRefresh";
            this.btnFastRefresh.UseVisualStyleBackColor = true;
            this.btnFastRefresh.Click += new System.EventHandler(this.btnFastRefresh_Click);
            // 
            // txtFastMinRssi
            // 
            resources.ApplyResources(this.txtFastMinRssi, "txtFastMinRssi");
            this.txtFastMinRssi.Name = "txtFastMinRssi";
            // 
            // btnSaveTags
            // 
            resources.ApplyResources(this.btnSaveTags, "btnSaveTags");
            this.btnSaveTags.ForeColor = System.Drawing.SystemColors.Desktop;
            this.btnSaveTags.Name = "btnSaveTags";
            this.btnSaveTags.UseVisualStyleBackColor = true;
            this.btnSaveTags.Click += new System.EventHandler(this.btnSaveTags_Click);
            // 
            // txtFastMaxRssi
            // 
            resources.ApplyResources(this.txtFastMaxRssi, "txtFastMaxRssi");
            this.txtFastMaxRssi.Name = "txtFastMaxRssi";
            // 
            // groupBox25
            // 
            resources.ApplyResources(this.groupBox25, "groupBox25");
            this.groupBox25.Controls.Add(this.led_total_tagreads);
            this.groupBox25.Controls.Add(this.label58);
            this.groupBox25.Controls.Add(this.led_totalread_count);
            this.groupBox25.Controls.Add(this.led_cmd_readrate);
            this.groupBox25.Controls.Add(this.label55);
            this.groupBox25.Controls.Add(this.label56);
            this.groupBox25.Controls.Add(this.led_cmd_execute_duration);
            this.groupBox25.Controls.Add(this.label57);
            this.groupBox25.Controls.Add(this.label54);
            this.groupBox25.Controls.Add(this.ledFast_total_execute_time);
            this.groupBox25.Name = "groupBox25";
            this.groupBox25.TabStop = false;
            // 
            // led_total_tagreads
            // 
            resources.ApplyResources(this.led_total_tagreads, "led_total_tagreads");
            this.led_total_tagreads.BackColor = System.Drawing.Color.Transparent;
            this.led_total_tagreads.BackColor_1 = System.Drawing.Color.Transparent;
            this.led_total_tagreads.BackColor_2 = System.Drawing.Color.DarkRed;
            this.led_total_tagreads.BevelRate = 0.1F;
            this.led_total_tagreads.BorderColor = System.Drawing.Color.Lavender;
            this.led_total_tagreads.BorderWidth = 3;
            this.led_total_tagreads.FadedColor = System.Drawing.SystemColors.ControlLight;
            this.led_total_tagreads.FocusedBorderColor = System.Drawing.Color.LightCoral;
            this.led_total_tagreads.ForeColor = System.Drawing.Color.MidnightBlue;
            this.led_total_tagreads.HighlightOpaque = ((byte)(20));
            this.led_total_tagreads.Name = "led_total_tagreads";
            this.led_total_tagreads.RoundCorner = true;
            this.led_total_tagreads.SegmentIntervalRatio = 50;
            this.led_total_tagreads.ShowHighlight = true;
            this.led_total_tagreads.TextAlignment = Led.Alignment.Right;
            // 
            // label58
            // 
            resources.ApplyResources(this.label58, "label58");
            this.label58.ForeColor = System.Drawing.SystemColors.ControlText;
            this.label58.Name = "label58";
            // 
            // led_totalread_count
            // 
            resources.ApplyResources(this.led_totalread_count, "led_totalread_count");
            this.led_totalread_count.BackColor = System.Drawing.Color.Transparent;
            this.led_totalread_count.BackColor_1 = System.Drawing.Color.Transparent;
            this.led_totalread_count.BackColor_2 = System.Drawing.Color.DarkRed;
            this.led_totalread_count.BevelRate = 0.1F;
            this.led_totalread_count.BorderColor = System.Drawing.Color.Lavender;
            this.led_totalread_count.FadedColor = System.Drawing.SystemColors.ControlLight;
            this.led_totalread_count.FocusedBorderColor = System.Drawing.Color.LightCoral;
            this.led_totalread_count.ForeColor = System.Drawing.Color.MidnightBlue;
            this.led_totalread_count.HighlightOpaque = ((byte)(20));
            this.led_totalread_count.Name = "led_totalread_count";
            this.led_totalread_count.RoundCorner = true;
            this.led_totalread_count.SegmentIntervalRatio = 50;
            this.led_totalread_count.ShowHighlight = true;
            this.led_totalread_count.TextAlignment = Led.Alignment.Right;
            this.led_totalread_count.TotalCharCount = 14;
            // 
            // led_cmd_readrate
            // 
            resources.ApplyResources(this.led_cmd_readrate, "led_cmd_readrate");
            this.led_cmd_readrate.BackColor = System.Drawing.Color.Transparent;
            this.led_cmd_readrate.BackColor_1 = System.Drawing.Color.Transparent;
            this.led_cmd_readrate.BackColor_2 = System.Drawing.Color.DarkRed;
            this.led_cmd_readrate.BevelRate = 0.1F;
            this.led_cmd_readrate.BorderColor = System.Drawing.Color.Lavender;
            this.led_cmd_readrate.FadedColor = System.Drawing.SystemColors.ControlLight;
            this.led_cmd_readrate.FocusedBorderColor = System.Drawing.Color.LightCoral;
            this.led_cmd_readrate.ForeColor = System.Drawing.Color.Purple;
            this.led_cmd_readrate.HighlightOpaque = ((byte)(20));
            this.led_cmd_readrate.Name = "led_cmd_readrate";
            this.led_cmd_readrate.RoundCorner = true;
            this.led_cmd_readrate.SegmentIntervalRatio = 50;
            this.led_cmd_readrate.ShowHighlight = true;
            this.led_cmd_readrate.TextAlignment = Led.Alignment.Right;
            this.led_cmd_readrate.TotalCharCount = 6;
            // 
            // label55
            // 
            resources.ApplyResources(this.label55, "label55");
            this.label55.ForeColor = System.Drawing.SystemColors.Desktop;
            this.label55.Name = "label55";
            // 
            // label56
            // 
            resources.ApplyResources(this.label56, "label56");
            this.label56.ForeColor = System.Drawing.SystemColors.Desktop;
            this.label56.Name = "label56";
            // 
            // led_cmd_execute_duration
            // 
            resources.ApplyResources(this.led_cmd_execute_duration, "led_cmd_execute_duration");
            this.led_cmd_execute_duration.BackColor = System.Drawing.Color.Transparent;
            this.led_cmd_execute_duration.BackColor_1 = System.Drawing.Color.Transparent;
            this.led_cmd_execute_duration.BackColor_2 = System.Drawing.Color.DarkRed;
            this.led_cmd_execute_duration.BevelRate = 0.1F;
            this.led_cmd_execute_duration.BorderColor = System.Drawing.Color.Lavender;
            this.led_cmd_execute_duration.FadedColor = System.Drawing.SystemColors.ControlLight;
            this.led_cmd_execute_duration.FocusedBorderColor = System.Drawing.Color.LightCoral;
            this.led_cmd_execute_duration.ForeColor = System.Drawing.Color.Purple;
            this.led_cmd_execute_duration.HighlightOpaque = ((byte)(20));
            this.led_cmd_execute_duration.Name = "led_cmd_execute_duration";
            this.led_cmd_execute_duration.RoundCorner = true;
            this.led_cmd_execute_duration.SegmentIntervalRatio = 50;
            this.led_cmd_execute_duration.ShowHighlight = true;
            this.led_cmd_execute_duration.TextAlignment = Led.Alignment.Right;
            this.led_cmd_execute_duration.TotalCharCount = 6;
            // 
            // label57
            // 
            resources.ApplyResources(this.label57, "label57");
            this.label57.ForeColor = System.Drawing.SystemColors.Desktop;
            this.label57.Name = "label57";
            // 
            // label54
            // 
            resources.ApplyResources(this.label54, "label54");
            this.label54.ForeColor = System.Drawing.SystemColors.Desktop;
            this.label54.Name = "label54";
            // 
            // ledFast_total_execute_time
            // 
            resources.ApplyResources(this.ledFast_total_execute_time, "ledFast_total_execute_time");
            this.ledFast_total_execute_time.BackColor = System.Drawing.Color.Transparent;
            this.ledFast_total_execute_time.BackColor_1 = System.Drawing.Color.Transparent;
            this.ledFast_total_execute_time.BackColor_2 = System.Drawing.Color.DarkRed;
            this.ledFast_total_execute_time.BevelRate = 0.1F;
            this.ledFast_total_execute_time.BorderColor = System.Drawing.Color.Lavender;
            this.ledFast_total_execute_time.FadedColor = System.Drawing.SystemColors.ControlLight;
            this.ledFast_total_execute_time.FocusedBorderColor = System.Drawing.Color.LightCoral;
            this.ledFast_total_execute_time.ForeColor = System.Drawing.Color.MidnightBlue;
            this.ledFast_total_execute_time.HighlightOpaque = ((byte)(20));
            this.ledFast_total_execute_time.Name = "ledFast_total_execute_time";
            this.ledFast_total_execute_time.RoundCorner = true;
            this.ledFast_total_execute_time.SegmentIntervalRatio = 50;
            this.ledFast_total_execute_time.ShowHighlight = true;
            this.ledFast_total_execute_time.TextAlignment = Led.Alignment.Right;
            this.ledFast_total_execute_time.TotalCharCount = 14;
            // 
            // groupBox2
            // 
            resources.ApplyResources(this.groupBox2, "groupBox2");
            this.groupBox2.Controls.Add(this.grb_inventory_type);
            this.groupBox2.Controls.Add(this.btnInventory);
            this.groupBox2.Controls.Add(this.groupBox27);
            this.groupBox2.Name = "groupBox2";
            this.groupBox2.TabStop = false;
            // 
            // grb_inventory_type
            // 
            resources.ApplyResources(this.grb_inventory_type, "grb_inventory_type");
            this.grb_inventory_type.Controls.Add(this.rb_fast_inv);
            this.grb_inventory_type.Controls.Add(this.radio_btn_fast_inv);
            this.grb_inventory_type.Controls.Add(this.radio_btn_realtime_inv);
            this.grb_inventory_type.Name = "grb_inventory_type";
            this.grb_inventory_type.TabStop = false;
            // 
            // rb_fast_inv
            // 
            resources.ApplyResources(this.rb_fast_inv, "rb_fast_inv");
            this.rb_fast_inv.Name = "rb_fast_inv";
            this.rb_fast_inv.TabStop = true;
            this.rb_fast_inv.UseVisualStyleBackColor = true;
            // 
            // radio_btn_fast_inv
            // 
            resources.ApplyResources(this.radio_btn_fast_inv, "radio_btn_fast_inv");
            this.radio_btn_fast_inv.Name = "radio_btn_fast_inv";
            this.radio_btn_fast_inv.TabStop = true;
            this.radio_btn_fast_inv.UseVisualStyleBackColor = true;
            this.radio_btn_fast_inv.CheckedChanged += new System.EventHandler(this.InventoryTypeChanged);
            // 
            // radio_btn_realtime_inv
            // 
            resources.ApplyResources(this.radio_btn_realtime_inv, "radio_btn_realtime_inv");
            this.radio_btn_realtime_inv.Name = "radio_btn_realtime_inv";
            this.radio_btn_realtime_inv.TabStop = true;
            this.radio_btn_realtime_inv.UseVisualStyleBackColor = true;
            this.radio_btn_realtime_inv.CheckedChanged += new System.EventHandler(this.InventoryTypeChanged);
            // 
            // btnInventory
            // 
            resources.ApplyResources(this.btnInventory, "btnInventory");
            this.btnInventory.ForeColor = System.Drawing.Color.DarkBlue;
            this.btnInventory.Name = "btnInventory";
            this.btnInventory.UseVisualStyleBackColor = true;
            this.btnInventory.Click += new System.EventHandler(this.btnInventory_Click_1);
            // 
            // groupBox27
            // 
            resources.ApplyResources(this.groupBox27, "groupBox27");
            this.groupBox27.Controls.Add(this.cb_InvTime);
            this.groupBox27.Controls.Add(this.label47);
            this.groupBox27.Controls.Add(this.tb_InvCntTime);
            this.groupBox27.Controls.Add(this.cb_IceBoxTest);
            this.groupBox27.Controls.Add(this.label69);
            this.groupBox27.Controls.Add(this.chkbxSaveLog);
            this.groupBox27.Controls.Add(this.chkbxReadBuffer);
            this.groupBox27.Controls.Add(this.cb_tagFocus);
            this.groupBox27.Controls.Add(this.tb_fast_inv_staytargetB_times);
            this.groupBox27.Controls.Add(this.lblInvExecTime);
            this.groupBox27.Controls.Add(this.mFastIntervalTime);
            this.groupBox27.Controls.Add(this.lblInvCmdInterval);
            this.groupBox27.Controls.Add(this.mInventoryExeCount);
            this.groupBox27.Controls.Add(this.cb_fast_inv_reverse_target);
            this.groupBox27.Name = "groupBox27";
            this.groupBox27.TabStop = false;
            // 
            // cb_InvTime
            // 
            resources.ApplyResources(this.cb_InvTime, "cb_InvTime");
            this.cb_InvTime.Name = "cb_InvTime";
            this.cb_InvTime.UseVisualStyleBackColor = true;
            this.cb_InvTime.CheckedChanged += new System.EventHandler(this.cb_InvTime_CheckedChanged);
            // 
            // label47
            // 
            resources.ApplyResources(this.label47, "label47");
            this.label47.Name = "label47";
            // 
            // tb_InvCntTime
            // 
            resources.ApplyResources(this.tb_InvCntTime, "tb_InvCntTime");
            this.tb_InvCntTime.Name = "tb_InvCntTime";
            // 
            // cb_IceBoxTest
            // 
            resources.ApplyResources(this.cb_IceBoxTest, "cb_IceBoxTest");
            this.cb_IceBoxTest.Name = "cb_IceBoxTest";
            this.cb_IceBoxTest.UseVisualStyleBackColor = true;
            this.cb_IceBoxTest.CheckedChanged += new System.EventHandler(this.cb_IceBoxTest_CheckedChanged);
            // 
            // label69
            // 
            resources.ApplyResources(this.label69, "label69");
            this.label69.ForeColor = System.Drawing.SystemColors.ControlText;
            this.label69.Name = "label69";
            // 
            // chkbxSaveLog
            // 
            resources.ApplyResources(this.chkbxSaveLog, "chkbxSaveLog");
            this.chkbxSaveLog.Name = "chkbxSaveLog";
            this.chkbxSaveLog.UseVisualStyleBackColor = true;
            this.chkbxSaveLog.CheckedChanged += new System.EventHandler(this.chkbxSaveLog_CheckedChanged);
            // 
            // chkbxReadBuffer
            // 
            resources.ApplyResources(this.chkbxReadBuffer, "chkbxReadBuffer");
            this.chkbxReadBuffer.Name = "chkbxReadBuffer";
            this.chkbxReadBuffer.UseVisualStyleBackColor = true;
            // 
            // cb_tagFocus
            // 
            resources.ApplyResources(this.cb_tagFocus, "cb_tagFocus");
            this.cb_tagFocus.Name = "cb_tagFocus";
            this.cb_tagFocus.UseVisualStyleBackColor = true;
            this.cb_tagFocus.CheckedChanged += new System.EventHandler(this.cb_tagFocus_CheckedChanged);
            // 
            // tb_fast_inv_staytargetB_times
            // 
            resources.ApplyResources(this.tb_fast_inv_staytargetB_times, "tb_fast_inv_staytargetB_times");
            this.tb_fast_inv_staytargetB_times.Name = "tb_fast_inv_staytargetB_times";
            // 
            // lblInvExecTime
            // 
            resources.ApplyResources(this.lblInvExecTime, "lblInvExecTime");
            this.lblInvExecTime.ForeColor = System.Drawing.SystemColors.ControlText;
            this.lblInvExecTime.Name = "lblInvExecTime";
            // 
            // mFastIntervalTime
            // 
            resources.ApplyResources(this.mFastIntervalTime, "mFastIntervalTime");
            this.mFastIntervalTime.Name = "mFastIntervalTime";
            // 
            // lblInvCmdInterval
            // 
            resources.ApplyResources(this.lblInvCmdInterval, "lblInvCmdInterval");
            this.lblInvCmdInterval.ForeColor = System.Drawing.SystemColors.ControlText;
            this.lblInvCmdInterval.Name = "lblInvCmdInterval";
            // 
            // mInventoryExeCount
            // 
            resources.ApplyResources(this.mInventoryExeCount, "mInventoryExeCount");
            this.mInventoryExeCount.Name = "mInventoryExeCount";
            // 
            // cb_fast_inv_reverse_target
            // 
            resources.ApplyResources(this.cb_fast_inv_reverse_target, "cb_fast_inv_reverse_target");
            this.cb_fast_inv_reverse_target.Name = "cb_fast_inv_reverse_target";
            this.cb_fast_inv_reverse_target.UseVisualStyleBackColor = true;
            this.cb_fast_inv_reverse_target.CheckedChanged += new System.EventHandler(this.cb_fast_inv_reverse_target_CheckedChanged);
            // 
            // pageAcessTag
            // 
            resources.ApplyResources(this.pageAcessTag, "pageAcessTag");
            this.pageAcessTag.BackColor = System.Drawing.Color.WhiteSmoke;
            this.pageAcessTag.Controls.Add(this.gbCmdOperateTag);
            this.pageAcessTag.Name = "pageAcessTag";
            this.pageAcessTag.UseVisualStyleBackColor = true;
            // 
            // gbCmdOperateTag
            // 
            resources.ApplyResources(this.gbCmdOperateTag, "gbCmdOperateTag");
            this.gbCmdOperateTag.Controls.Add(this.cbMulAnt);
            this.gbCmdOperateTag.Controls.Add(this.groupBox14);
            this.gbCmdOperateTag.Controls.Add(this.chkbxReadTagMultiBankEn);
            this.gbCmdOperateTag.Controls.Add(this.btnStartReadSensorTag);
            this.gbCmdOperateTag.Controls.Add(this.chkbxReadSensorTag);
            this.gbCmdOperateTag.Controls.Add(this.grbSensorType);
            this.gbCmdOperateTag.Controls.Add(this.btnClearTagOpResult);
            this.gbCmdOperateTag.Controls.Add(this.btnReadTag);
            this.gbCmdOperateTag.Controls.Add(this.groupBox28);
            this.gbCmdOperateTag.Controls.Add(this.grbReadTagMultiBank);
            this.gbCmdOperateTag.Controls.Add(this.dgvTagOp);
            this.gbCmdOperateTag.Controls.Add(this.groupBox3);
            this.gbCmdOperateTag.Controls.Add(this.groupBox31);
            this.gbCmdOperateTag.Controls.Add(this.groupBox16);
            this.gbCmdOperateTag.Controls.Add(this.groupBox15);
            this.gbCmdOperateTag.Controls.Add(this.groupBox13);
            this.gbCmdOperateTag.Name = "gbCmdOperateTag";
            this.gbCmdOperateTag.TabStop = false;
            // 
            // cbMulAnt
            // 
            resources.ApplyResources(this.cbMulAnt, "cbMulAnt");
            this.cbMulAnt.Name = "cbMulAnt";
            this.cbMulAnt.UseVisualStyleBackColor = true;
            this.cbMulAnt.CheckedChanged += new System.EventHandler(this.cbMulAnt_CheckedChanged);
            // 
            // groupBox14
            // 
            resources.ApplyResources(this.groupBox14, "groupBox14");
            this.groupBox14.Controls.Add(this.btnSetTagOpWorkAnt);
            this.groupBox14.Controls.Add(this.btnGetTagOpWorkAnt);
            this.groupBox14.Controls.Add(this.cmbbxTagOpWorkAnt);
            this.groupBox14.ForeColor = System.Drawing.Color.Black;
            this.groupBox14.Name = "groupBox14";
            this.groupBox14.TabStop = false;
            // 
            // btnSetTagOpWorkAnt
            // 
            resources.ApplyResources(this.btnSetTagOpWorkAnt, "btnSetTagOpWorkAnt");
            this.btnSetTagOpWorkAnt.Name = "btnSetTagOpWorkAnt";
            this.btnSetTagOpWorkAnt.UseVisualStyleBackColor = true;
            this.btnSetTagOpWorkAnt.Click += new System.EventHandler(this.btnSetTagOpWorkAnt_Click);
            // 
            // btnGetTagOpWorkAnt
            // 
            resources.ApplyResources(this.btnGetTagOpWorkAnt, "btnGetTagOpWorkAnt");
            this.btnGetTagOpWorkAnt.Name = "btnGetTagOpWorkAnt";
            this.btnGetTagOpWorkAnt.UseVisualStyleBackColor = true;
            this.btnGetTagOpWorkAnt.Click += new System.EventHandler(this.btnGetTagOpWorkAnt_Click);
            // 
            // cmbbxTagOpWorkAnt
            // 
            resources.ApplyResources(this.cmbbxTagOpWorkAnt, "cmbbxTagOpWorkAnt");
            this.cmbbxTagOpWorkAnt.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbbxTagOpWorkAnt.FormattingEnabled = true;
            this.cmbbxTagOpWorkAnt.Name = "cmbbxTagOpWorkAnt";
            // 
            // chkbxReadTagMultiBankEn
            // 
            resources.ApplyResources(this.chkbxReadTagMultiBankEn, "chkbxReadTagMultiBankEn");
            this.chkbxReadTagMultiBankEn.Name = "chkbxReadTagMultiBankEn";
            this.chkbxReadTagMultiBankEn.UseVisualStyleBackColor = true;
            this.chkbxReadTagMultiBankEn.CheckedChanged += new System.EventHandler(this.chkbxReadTagMultiBankEn_CheckedChanged);
            // 
            // btnStartReadSensorTag
            // 
            resources.ApplyResources(this.btnStartReadSensorTag, "btnStartReadSensorTag");
            this.btnStartReadSensorTag.Name = "btnStartReadSensorTag";
            this.btnStartReadSensorTag.UseVisualStyleBackColor = true;
            this.btnStartReadSensorTag.Click += new System.EventHandler(this.btnStartReadSensorTag_Click);
            // 
            // chkbxReadSensorTag
            // 
            resources.ApplyResources(this.chkbxReadSensorTag, "chkbxReadSensorTag");
            this.chkbxReadSensorTag.Name = "chkbxReadSensorTag";
            this.chkbxReadSensorTag.UseVisualStyleBackColor = true;
            this.chkbxReadSensorTag.CheckedChanged += new System.EventHandler(this.chkbxReadSensorTag_CheckedChanged);
            // 
            // grbSensorType
            // 
            resources.ApplyResources(this.grbSensorType, "grbSensorType");
            this.grbSensorType.Controls.Add(this.radio_btn_johar_1);
            this.grbSensorType.Name = "grbSensorType";
            this.grbSensorType.TabStop = false;
            // 
            // radio_btn_johar_1
            // 
            resources.ApplyResources(this.radio_btn_johar_1, "radio_btn_johar_1");
            this.radio_btn_johar_1.Name = "radio_btn_johar_1";
            this.radio_btn_johar_1.TabStop = true;
            this.radio_btn_johar_1.UseVisualStyleBackColor = true;
            // 
            // btnClearTagOpResult
            // 
            resources.ApplyResources(this.btnClearTagOpResult, "btnClearTagOpResult");
            this.btnClearTagOpResult.Name = "btnClearTagOpResult";
            this.btnClearTagOpResult.UseVisualStyleBackColor = true;
            this.btnClearTagOpResult.Click += new System.EventHandler(this.btnClearTagOpResult_Click);
            // 
            // btnReadTag
            // 
            resources.ApplyResources(this.btnReadTag, "btnReadTag");
            this.btnReadTag.Name = "btnReadTag";
            this.btnReadTag.UseVisualStyleBackColor = true;
            this.btnReadTag.Click += new System.EventHandler(this.btnReadTag_Click);
            // 
            // groupBox28
            // 
            resources.ApplyResources(this.groupBox28, "groupBox28");
            this.groupBox28.Controls.Add(this.label24);
            this.groupBox28.Controls.Add(this.radio_btnBlockWrite);
            this.groupBox28.Controls.Add(this.hexTb_WriteData);
            this.groupBox28.Controls.Add(this.btnWriteTag);
            this.groupBox28.Controls.Add(this.radio_btnWrite);
            this.groupBox28.Name = "groupBox28";
            this.groupBox28.TabStop = false;
            // 
            // label24
            // 
            resources.ApplyResources(this.label24, "label24");
            this.label24.Name = "label24";
            // 
            // radio_btnBlockWrite
            // 
            resources.ApplyResources(this.radio_btnBlockWrite, "radio_btnBlockWrite");
            this.radio_btnBlockWrite.Checked = true;
            this.radio_btnBlockWrite.Name = "radio_btnBlockWrite";
            this.radio_btnBlockWrite.TabStop = true;
            this.radio_btnBlockWrite.UseVisualStyleBackColor = true;
            // 
            // hexTb_WriteData
            // 
            resources.ApplyResources(this.hexTb_WriteData, "hexTb_WriteData");
            this.hexTb_WriteData.Name = "hexTb_WriteData";
            // 
            // btnWriteTag
            // 
            resources.ApplyResources(this.btnWriteTag, "btnWriteTag");
            this.btnWriteTag.Name = "btnWriteTag";
            this.btnWriteTag.UseVisualStyleBackColor = true;
            this.btnWriteTag.Click += new System.EventHandler(this.btnWriteTag_Click);
            // 
            // radio_btnWrite
            // 
            resources.ApplyResources(this.radio_btnWrite, "radio_btnWrite");
            this.radio_btnWrite.Name = "radio_btnWrite";
            this.radio_btnWrite.UseVisualStyleBackColor = true;
            // 
            // grbReadTagMultiBank
            // 
            resources.ApplyResources(this.grbReadTagMultiBank, "grbReadTagMultiBank");
            this.grbReadTagMultiBank.Controls.Add(this.cmbbxReadTagReadMode);
            this.grbReadTagMultiBank.Controls.Add(this.cmbbxReadTagTarget);
            this.grbReadTagMultiBank.Controls.Add(this.cmbbxReadTagSession);
            this.grbReadTagMultiBank.Controls.Add(this.label68);
            this.grbReadTagMultiBank.Controls.Add(this.label67);
            this.grbReadTagMultiBank.Controls.Add(this.label66);
            this.grbReadTagMultiBank.Controls.Add(this.txtbxReadTagUserCnt);
            this.grbReadTagMultiBank.Controls.Add(this.label64);
            this.grbReadTagMultiBank.Controls.Add(this.txtbxReadTagUserAddr);
            this.grbReadTagMultiBank.Controls.Add(this.label65);
            this.grbReadTagMultiBank.Controls.Add(this.txtbxReadTagTidCnt);
            this.grbReadTagMultiBank.Controls.Add(this.label59);
            this.grbReadTagMultiBank.Controls.Add(this.txtbxReadTagTidAddr);
            this.grbReadTagMultiBank.Controls.Add(this.label63);
            this.grbReadTagMultiBank.Controls.Add(this.txtbxReadTagResCnt);
            this.grbReadTagMultiBank.Controls.Add(this.label28);
            this.grbReadTagMultiBank.Controls.Add(this.txtbxReadTagResAddr);
            this.grbReadTagMultiBank.Controls.Add(this.label25);
            this.grbReadTagMultiBank.Name = "grbReadTagMultiBank";
            this.grbReadTagMultiBank.TabStop = false;
            // 
            // cmbbxReadTagReadMode
            // 
            resources.ApplyResources(this.cmbbxReadTagReadMode, "cmbbxReadTagReadMode");
            this.cmbbxReadTagReadMode.FormattingEnabled = true;
            this.cmbbxReadTagReadMode.Name = "cmbbxReadTagReadMode";
            // 
            // cmbbxReadTagTarget
            // 
            resources.ApplyResources(this.cmbbxReadTagTarget, "cmbbxReadTagTarget");
            this.cmbbxReadTagTarget.FormattingEnabled = true;
            this.cmbbxReadTagTarget.Name = "cmbbxReadTagTarget";
            // 
            // cmbbxReadTagSession
            // 
            resources.ApplyResources(this.cmbbxReadTagSession, "cmbbxReadTagSession");
            this.cmbbxReadTagSession.FormattingEnabled = true;
            this.cmbbxReadTagSession.Name = "cmbbxReadTagSession";
            // 
            // label68
            // 
            resources.ApplyResources(this.label68, "label68");
            this.label68.Name = "label68";
            // 
            // label67
            // 
            resources.ApplyResources(this.label67, "label67");
            this.label67.Name = "label67";
            // 
            // label66
            // 
            resources.ApplyResources(this.label66, "label66");
            this.label66.Name = "label66";
            // 
            // txtbxReadTagUserCnt
            // 
            resources.ApplyResources(this.txtbxReadTagUserCnt, "txtbxReadTagUserCnt");
            this.txtbxReadTagUserCnt.Name = "txtbxReadTagUserCnt";
            // 
            // label64
            // 
            resources.ApplyResources(this.label64, "label64");
            this.label64.Name = "label64";
            // 
            // txtbxReadTagUserAddr
            // 
            resources.ApplyResources(this.txtbxReadTagUserAddr, "txtbxReadTagUserAddr");
            this.txtbxReadTagUserAddr.Name = "txtbxReadTagUserAddr";
            // 
            // label65
            // 
            resources.ApplyResources(this.label65, "label65");
            this.label65.Name = "label65";
            // 
            // txtbxReadTagTidCnt
            // 
            resources.ApplyResources(this.txtbxReadTagTidCnt, "txtbxReadTagTidCnt");
            this.txtbxReadTagTidCnt.Name = "txtbxReadTagTidCnt";
            // 
            // label59
            // 
            resources.ApplyResources(this.label59, "label59");
            this.label59.Name = "label59";
            // 
            // txtbxReadTagTidAddr
            // 
            resources.ApplyResources(this.txtbxReadTagTidAddr, "txtbxReadTagTidAddr");
            this.txtbxReadTagTidAddr.Name = "txtbxReadTagTidAddr";
            // 
            // label63
            // 
            resources.ApplyResources(this.label63, "label63");
            this.label63.Name = "label63";
            // 
            // txtbxReadTagResCnt
            // 
            resources.ApplyResources(this.txtbxReadTagResCnt, "txtbxReadTagResCnt");
            this.txtbxReadTagResCnt.Name = "txtbxReadTagResCnt";
            // 
            // label28
            // 
            resources.ApplyResources(this.label28, "label28");
            this.label28.Name = "label28";
            // 
            // txtbxReadTagResAddr
            // 
            resources.ApplyResources(this.txtbxReadTagResAddr, "txtbxReadTagResAddr");
            this.txtbxReadTagResAddr.Name = "txtbxReadTagResAddr";
            // 
            // label25
            // 
            resources.ApplyResources(this.label25, "label25");
            this.label25.Name = "label25";
            // 
            // dgvTagOp
            // 
            resources.ApplyResources(this.dgvTagOp, "dgvTagOp");
            this.dgvTagOp.ColumnHeadersHeightSizeMode = System.Windows.Forms.DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            this.dgvTagOp.Columns.AddRange(new System.Windows.Forms.DataGridViewColumn[] {
            this.tagOp_SerialNumberColumn,
            this.tagOp_PcColumn,
            this.tagOp_CrcColumn,
            this.tagOp_EpcColumn,
            this.tagOp_DataColumn,
            this.tagOp_DataLenColumn,
            this.tagOp_AntennaColumn,
            this.tagOp_OpCountColumn,
            this.tagOp_FreqColumn,
            this.tagOp_TemperatureColumn});
            this.dgvTagOp.Name = "dgvTagOp";
            this.dgvTagOp.RowTemplate.Height = 23;
            // 
            // tagOp_SerialNumberColumn
            // 
            resources.ApplyResources(this.tagOp_SerialNumberColumn, "tagOp_SerialNumberColumn");
            this.tagOp_SerialNumberColumn.Name = "tagOp_SerialNumberColumn";
            // 
            // tagOp_PcColumn
            // 
            resources.ApplyResources(this.tagOp_PcColumn, "tagOp_PcColumn");
            this.tagOp_PcColumn.Name = "tagOp_PcColumn";
            // 
            // tagOp_CrcColumn
            // 
            resources.ApplyResources(this.tagOp_CrcColumn, "tagOp_CrcColumn");
            this.tagOp_CrcColumn.Name = "tagOp_CrcColumn";
            // 
            // tagOp_EpcColumn
            // 
            resources.ApplyResources(this.tagOp_EpcColumn, "tagOp_EpcColumn");
            this.tagOp_EpcColumn.Name = "tagOp_EpcColumn";
            // 
            // tagOp_DataColumn
            // 
            resources.ApplyResources(this.tagOp_DataColumn, "tagOp_DataColumn");
            this.tagOp_DataColumn.Name = "tagOp_DataColumn";
            // 
            // tagOp_DataLenColumn
            // 
            resources.ApplyResources(this.tagOp_DataLenColumn, "tagOp_DataLenColumn");
            this.tagOp_DataLenColumn.Name = "tagOp_DataLenColumn";
            // 
            // tagOp_AntennaColumn
            // 
            resources.ApplyResources(this.tagOp_AntennaColumn, "tagOp_AntennaColumn");
            this.tagOp_AntennaColumn.Name = "tagOp_AntennaColumn";
            // 
            // tagOp_OpCountColumn
            // 
            resources.ApplyResources(this.tagOp_OpCountColumn, "tagOp_OpCountColumn");
            this.tagOp_OpCountColumn.Name = "tagOp_OpCountColumn";
            // 
            // tagOp_FreqColumn
            // 
            resources.ApplyResources(this.tagOp_FreqColumn, "tagOp_FreqColumn");
            this.tagOp_FreqColumn.Name = "tagOp_FreqColumn";
            // 
            // tagOp_TemperatureColumn
            // 
            resources.ApplyResources(this.tagOp_TemperatureColumn, "tagOp_TemperatureColumn");
            this.tagOp_TemperatureColumn.Name = "tagOp_TemperatureColumn";
            // 
            // groupBox3
            // 
            resources.ApplyResources(this.groupBox3, "groupBox3");
            this.groupBox3.Controls.Add(this.hexTb_accessPw);
            this.groupBox3.Name = "groupBox3";
            this.groupBox3.TabStop = false;
            // 
            // hexTb_accessPw
            // 
            resources.ApplyResources(this.hexTb_accessPw, "hexTb_accessPw");
            this.hexTb_accessPw.Name = "hexTb_accessPw";
            // 
            // groupBox31
            // 
            resources.ApplyResources(this.groupBox31, "groupBox31");
            this.groupBox31.Controls.Add(this.rdbUser);
            this.groupBox31.Controls.Add(this.label26);
            this.groupBox31.Controls.Add(this.tb_startWord);
            this.groupBox31.Controls.Add(this.rdbTid);
            this.groupBox31.Controls.Add(this.label27);
            this.groupBox31.Controls.Add(this.tb_wordLen);
            this.groupBox31.Controls.Add(this.rdbEpc);
            this.groupBox31.Controls.Add(this.rdbReserved);
            this.groupBox31.Name = "groupBox31";
            this.groupBox31.TabStop = false;
            // 
            // rdbUser
            // 
            resources.ApplyResources(this.rdbUser, "rdbUser");
            this.rdbUser.Name = "rdbUser";
            this.rdbUser.TabStop = true;
            this.rdbUser.UseVisualStyleBackColor = true;
            this.rdbUser.CheckedChanged += new System.EventHandler(this.MembankCheckChanged);
            // 
            // label26
            // 
            resources.ApplyResources(this.label26, "label26");
            this.label26.Name = "label26";
            // 
            // tb_startWord
            // 
            resources.ApplyResources(this.tb_startWord, "tb_startWord");
            this.tb_startWord.Name = "tb_startWord";
            // 
            // rdbTid
            // 
            resources.ApplyResources(this.rdbTid, "rdbTid");
            this.rdbTid.Name = "rdbTid";
            this.rdbTid.TabStop = true;
            this.rdbTid.UseVisualStyleBackColor = true;
            this.rdbTid.CheckedChanged += new System.EventHandler(this.MembankCheckChanged);
            // 
            // label27
            // 
            resources.ApplyResources(this.label27, "label27");
            this.label27.Name = "label27";
            // 
            // tb_wordLen
            // 
            resources.ApplyResources(this.tb_wordLen, "tb_wordLen");
            this.tb_wordLen.Name = "tb_wordLen";
            // 
            // rdbEpc
            // 
            resources.ApplyResources(this.rdbEpc, "rdbEpc");
            this.rdbEpc.Name = "rdbEpc";
            this.rdbEpc.TabStop = true;
            this.rdbEpc.UseVisualStyleBackColor = true;
            this.rdbEpc.CheckedChanged += new System.EventHandler(this.MembankCheckChanged);
            // 
            // rdbReserved
            // 
            resources.ApplyResources(this.rdbReserved, "rdbReserved");
            this.rdbReserved.Name = "rdbReserved";
            this.rdbReserved.TabStop = true;
            this.rdbReserved.UseVisualStyleBackColor = true;
            this.rdbReserved.CheckedChanged += new System.EventHandler(this.MembankCheckChanged);
            // 
            // groupBox16
            // 
            resources.ApplyResources(this.groupBox16, "groupBox16");
            this.groupBox16.Controls.Add(this.btnKillTag);
            this.groupBox16.Controls.Add(this.htxtKillPwd);
            this.groupBox16.Controls.Add(this.label29);
            this.groupBox16.Name = "groupBox16";
            this.groupBox16.TabStop = false;
            // 
            // btnKillTag
            // 
            resources.ApplyResources(this.btnKillTag, "btnKillTag");
            this.btnKillTag.Name = "btnKillTag";
            this.btnKillTag.UseVisualStyleBackColor = true;
            this.btnKillTag.Click += new System.EventHandler(this.btnKillTag_Click);
            // 
            // htxtKillPwd
            // 
            resources.ApplyResources(this.htxtKillPwd, "htxtKillPwd");
            this.htxtKillPwd.Name = "htxtKillPwd";
            // 
            // label29
            // 
            resources.ApplyResources(this.label29, "label29");
            this.label29.Name = "label29";
            // 
            // groupBox15
            // 
            resources.ApplyResources(this.groupBox15, "groupBox15");
            this.groupBox15.Controls.Add(this.groupBox19);
            this.groupBox15.Controls.Add(this.groupBox18);
            this.groupBox15.Controls.Add(this.btnLockTag);
            this.groupBox15.Name = "groupBox15";
            this.groupBox15.TabStop = false;
            // 
            // groupBox19
            // 
            resources.ApplyResources(this.groupBox19, "groupBox19");
            this.groupBox19.Controls.Add(this.rdbUserMemory);
            this.groupBox19.Controls.Add(this.rdbTidMemory);
            this.groupBox19.Controls.Add(this.rdbEpcMermory);
            this.groupBox19.Controls.Add(this.rdbKillPwd);
            this.groupBox19.Controls.Add(this.rdbAccessPwd);
            this.groupBox19.Name = "groupBox19";
            this.groupBox19.TabStop = false;
            // 
            // rdbUserMemory
            // 
            resources.ApplyResources(this.rdbUserMemory, "rdbUserMemory");
            this.rdbUserMemory.Name = "rdbUserMemory";
            this.rdbUserMemory.TabStop = true;
            this.rdbUserMemory.UseVisualStyleBackColor = true;
            // 
            // rdbTidMemory
            // 
            resources.ApplyResources(this.rdbTidMemory, "rdbTidMemory");
            this.rdbTidMemory.Name = "rdbTidMemory";
            this.rdbTidMemory.TabStop = true;
            this.rdbTidMemory.UseVisualStyleBackColor = true;
            // 
            // rdbEpcMermory
            // 
            resources.ApplyResources(this.rdbEpcMermory, "rdbEpcMermory");
            this.rdbEpcMermory.Name = "rdbEpcMermory";
            this.rdbEpcMermory.TabStop = true;
            this.rdbEpcMermory.UseVisualStyleBackColor = true;
            // 
            // rdbKillPwd
            // 
            resources.ApplyResources(this.rdbKillPwd, "rdbKillPwd");
            this.rdbKillPwd.Name = "rdbKillPwd";
            this.rdbKillPwd.TabStop = true;
            this.rdbKillPwd.UseVisualStyleBackColor = true;
            // 
            // rdbAccessPwd
            // 
            resources.ApplyResources(this.rdbAccessPwd, "rdbAccessPwd");
            this.rdbAccessPwd.Name = "rdbAccessPwd";
            this.rdbAccessPwd.TabStop = true;
            this.rdbAccessPwd.UseVisualStyleBackColor = true;
            // 
            // groupBox18
            // 
            resources.ApplyResources(this.groupBox18, "groupBox18");
            this.groupBox18.Controls.Add(this.rdbLockEver);
            this.groupBox18.Controls.Add(this.rdbFreeEver);
            this.groupBox18.Controls.Add(this.rdbLock);
            this.groupBox18.Controls.Add(this.rdbFree);
            this.groupBox18.Name = "groupBox18";
            this.groupBox18.TabStop = false;
            // 
            // rdbLockEver
            // 
            resources.ApplyResources(this.rdbLockEver, "rdbLockEver");
            this.rdbLockEver.Name = "rdbLockEver";
            this.rdbLockEver.TabStop = true;
            this.rdbLockEver.UseVisualStyleBackColor = true;
            // 
            // rdbFreeEver
            // 
            resources.ApplyResources(this.rdbFreeEver, "rdbFreeEver");
            this.rdbFreeEver.Name = "rdbFreeEver";
            this.rdbFreeEver.TabStop = true;
            this.rdbFreeEver.UseVisualStyleBackColor = true;
            // 
            // rdbLock
            // 
            resources.ApplyResources(this.rdbLock, "rdbLock");
            this.rdbLock.Name = "rdbLock";
            this.rdbLock.TabStop = true;
            this.rdbLock.UseVisualStyleBackColor = true;
            // 
            // rdbFree
            // 
            resources.ApplyResources(this.rdbFree, "rdbFree");
            this.rdbFree.Name = "rdbFree";
            this.rdbFree.TabStop = true;
            this.rdbFree.UseVisualStyleBackColor = true;
            // 
            // btnLockTag
            // 
            resources.ApplyResources(this.btnLockTag, "btnLockTag");
            this.btnLockTag.Name = "btnLockTag";
            this.btnLockTag.UseVisualStyleBackColor = true;
            this.btnLockTag.Click += new System.EventHandler(this.btnLockTag_Click);
            // 
            // groupBox13
            // 
            resources.ApplyResources(this.groupBox13, "groupBox13");
            this.groupBox13.Controls.Add(this.btnCancelAccessEpcMatch);
            this.groupBox13.Controls.Add(this.btnGetAccessEpcMatch);
            this.groupBox13.Controls.Add(this.label23);
            this.groupBox13.Controls.Add(this.btnSetAccessEpcMatch);
            this.groupBox13.Controls.Add(this.cmbSetAccessEpcMatch);
            this.groupBox13.Controls.Add(this.txtAccessEpcMatch);
            this.groupBox13.Name = "groupBox13";
            this.groupBox13.TabStop = false;
            // 
            // btnCancelAccessEpcMatch
            // 
            resources.ApplyResources(this.btnCancelAccessEpcMatch, "btnCancelAccessEpcMatch");
            this.btnCancelAccessEpcMatch.Name = "btnCancelAccessEpcMatch";
            this.btnCancelAccessEpcMatch.UseVisualStyleBackColor = true;
            this.btnCancelAccessEpcMatch.Click += new System.EventHandler(this.btnCancelAccessEpcMatch_Click);
            // 
            // btnGetAccessEpcMatch
            // 
            resources.ApplyResources(this.btnGetAccessEpcMatch, "btnGetAccessEpcMatch");
            this.btnGetAccessEpcMatch.Name = "btnGetAccessEpcMatch";
            this.btnGetAccessEpcMatch.UseVisualStyleBackColor = true;
            this.btnGetAccessEpcMatch.Click += new System.EventHandler(this.btnGetAccessEpcMatch_Click);
            // 
            // label23
            // 
            resources.ApplyResources(this.label23, "label23");
            this.label23.Name = "label23";
            // 
            // btnSetAccessEpcMatch
            // 
            resources.ApplyResources(this.btnSetAccessEpcMatch, "btnSetAccessEpcMatch");
            this.btnSetAccessEpcMatch.Name = "btnSetAccessEpcMatch";
            this.btnSetAccessEpcMatch.UseVisualStyleBackColor = true;
            this.btnSetAccessEpcMatch.Click += new System.EventHandler(this.btnSetAccessEpcMatch_Click);
            // 
            // cmbSetAccessEpcMatch
            // 
            resources.ApplyResources(this.cmbSetAccessEpcMatch, "cmbSetAccessEpcMatch");
            this.cmbSetAccessEpcMatch.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbSetAccessEpcMatch.FormattingEnabled = true;
            this.cmbSetAccessEpcMatch.Name = "cmbSetAccessEpcMatch";
            this.cmbSetAccessEpcMatch.DropDown += new System.EventHandler(this.cmbSetAccessEpcMatch_DropDown);
            // 
            // txtAccessEpcMatch
            // 
            resources.ApplyResources(this.txtAccessEpcMatch, "txtAccessEpcMatch");
            this.txtAccessEpcMatch.Name = "txtAccessEpcMatch";
            this.txtAccessEpcMatch.ReadOnly = true;
            // 
            // PagTranDataLog
            // 
            resources.ApplyResources(this.PagTranDataLog, "PagTranDataLog");
            this.PagTranDataLog.BackColor = System.Drawing.Color.WhiteSmoke;
            this.PagTranDataLog.Controls.Add(this.lrtxtDataTran);
            this.PagTranDataLog.Controls.Add(this.panel3);
            this.PagTranDataLog.Name = "PagTranDataLog";
            this.PagTranDataLog.UseVisualStyleBackColor = true;
            // 
            // lrtxtDataTran
            // 
            resources.ApplyResources(this.lrtxtDataTran, "lrtxtDataTran");
            this.lrtxtDataTran.Name = "lrtxtDataTran";
            this.lrtxtDataTran.DoubleClick += new System.EventHandler(this.lrtxtDataTran_DoubleClick);
            // 
            // panel3
            // 
            resources.ApplyResources(this.panel3, "panel3");
            this.panel3.Controls.Add(this.label16);
            this.panel3.Controls.Add(this.htxtSendData);
            this.panel3.Controls.Add(this.btnSaveData);
            this.panel3.Controls.Add(this.btnClearData);
            this.panel3.Controls.Add(this.htxtCheckData);
            this.panel3.Controls.Add(this.label17);
            this.panel3.Controls.Add(this.btnSendData);
            this.panel3.Name = "panel3";
            // 
            // label16
            // 
            resources.ApplyResources(this.label16, "label16");
            this.label16.Name = "label16";
            // 
            // htxtSendData
            // 
            resources.ApplyResources(this.htxtSendData, "htxtSendData");
            this.htxtSendData.Name = "htxtSendData";
            this.htxtSendData.Leave += new System.EventHandler(this.htxtSendData_Leave);
            // 
            // btnSaveData
            // 
            resources.ApplyResources(this.btnSaveData, "btnSaveData");
            this.btnSaveData.Name = "btnSaveData";
            this.btnSaveData.UseVisualStyleBackColor = true;
            this.btnSaveData.Click += new System.EventHandler(this.btnSaveData_Click);
            // 
            // btnClearData
            // 
            resources.ApplyResources(this.btnClearData, "btnClearData");
            this.btnClearData.Name = "btnClearData";
            this.btnClearData.UseVisualStyleBackColor = true;
            this.btnClearData.Click += new System.EventHandler(this.btnClearData_Click);
            // 
            // htxtCheckData
            // 
            resources.ApplyResources(this.htxtCheckData, "htxtCheckData");
            this.htxtCheckData.Name = "htxtCheckData";
            this.htxtCheckData.ReadOnly = true;
            // 
            // label17
            // 
            resources.ApplyResources(this.label17, "label17");
            this.label17.Name = "label17";
            // 
            // btnSendData
            // 
            resources.ApplyResources(this.btnSendData, "btnSendData");
            this.btnSendData.Name = "btnSendData";
            this.btnSendData.UseVisualStyleBackColor = true;
            this.btnSendData.Click += new System.EventHandler(this.btnSendData_Click);
            // 
            // net_configure_tabPage
            // 
            resources.ApplyResources(this.net_configure_tabPage, "net_configure_tabPage");
            this.net_configure_tabPage.Controls.Add(this.groupBox20);
            this.net_configure_tabPage.Controls.Add(this.groupBox17);
            this.net_configure_tabPage.Controls.Add(this.lblNetPortCount);
            this.net_configure_tabPage.Controls.Add(this.port_setting_tabcontrol);
            this.net_configure_tabPage.Controls.Add(this.btnClearNetPort);
            this.net_configure_tabPage.Controls.Add(this.net_base_settings_gb);
            this.net_configure_tabPage.Controls.Add(this.dgvNetPort);
            this.net_configure_tabPage.Controls.Add(this.label159);
            this.net_configure_tabPage.Controls.Add(this.cmbbxNetCard);
            this.net_configure_tabPage.Controls.Add(this.groupBox30);
            this.net_configure_tabPage.Controls.Add(this.btnSearchNetport);
            this.net_configure_tabPage.Controls.Add(this.net_refresh_netcard_btn);
            this.net_configure_tabPage.Name = "net_configure_tabPage";
            this.net_configure_tabPage.UseVisualStyleBackColor = true;
            // 
            // groupBox20
            // 
            resources.ApplyResources(this.groupBox20, "groupBox20");
            this.groupBox20.Controls.Add(this.btnGetNetport);
            this.groupBox20.Controls.Add(this.btnSetNetport);
            this.groupBox20.Controls.Add(this.net_load_cfg_btn);
            this.groupBox20.Controls.Add(this.btnResetNetport);
            this.groupBox20.Controls.Add(this.net_save_cfg_btn);
            this.groupBox20.Controls.Add(this.btnDefaultNetPort);
            this.groupBox20.Name = "groupBox20";
            this.groupBox20.TabStop = false;
            // 
            // btnGetNetport
            // 
            resources.ApplyResources(this.btnGetNetport, "btnGetNetport");
            this.btnGetNetport.Name = "btnGetNetport";
            this.btnGetNetport.UseVisualStyleBackColor = true;
            this.btnGetNetport.Click += new System.EventHandler(this.btnGetNetport_Click);
            // 
            // btnSetNetport
            // 
            resources.ApplyResources(this.btnSetNetport, "btnSetNetport");
            this.btnSetNetport.Name = "btnSetNetport";
            this.btnSetNetport.UseVisualStyleBackColor = true;
            this.btnSetNetport.Click += new System.EventHandler(this.btnSetNetport_Click);
            // 
            // net_load_cfg_btn
            // 
            resources.ApplyResources(this.net_load_cfg_btn, "net_load_cfg_btn");
            this.net_load_cfg_btn.Name = "net_load_cfg_btn";
            this.net_load_cfg_btn.UseVisualStyleBackColor = true;
            this.net_load_cfg_btn.Click += new System.EventHandler(this.btnLoadCfgFromFile_Click);
            // 
            // btnResetNetport
            // 
            resources.ApplyResources(this.btnResetNetport, "btnResetNetport");
            this.btnResetNetport.Name = "btnResetNetport";
            this.btnResetNetport.UseVisualStyleBackColor = true;
            this.btnResetNetport.Click += new System.EventHandler(this.btnResetNetport_Click);
            // 
            // net_save_cfg_btn
            // 
            resources.ApplyResources(this.net_save_cfg_btn, "net_save_cfg_btn");
            this.net_save_cfg_btn.Name = "net_save_cfg_btn";
            this.net_save_cfg_btn.UseVisualStyleBackColor = true;
            this.net_save_cfg_btn.Click += new System.EventHandler(this.btnStoreCfgToFile_Click);
            // 
            // btnDefaultNetPort
            // 
            resources.ApplyResources(this.btnDefaultNetPort, "btnDefaultNetPort");
            this.btnDefaultNetPort.Name = "btnDefaultNetPort";
            this.btnDefaultNetPort.UseVisualStyleBackColor = true;
            this.btnDefaultNetPort.Click += new System.EventHandler(this.btnDefaultNetPort_Click);
            // 
            // groupBox17
            // 
            resources.ApplyResources(this.groupBox17, "groupBox17");
            this.groupBox17.Controls.Add(this.linklblOldNetPortCfgTool_Link);
            this.groupBox17.Controls.Add(this.label164);
            this.groupBox17.Controls.Add(this.label165);
            this.groupBox17.Controls.Add(this.linklblNetPortCfgTool_Link);
            this.groupBox17.Name = "groupBox17";
            this.groupBox17.TabStop = false;
            // 
            // linklblOldNetPortCfgTool_Link
            // 
            resources.ApplyResources(this.linklblOldNetPortCfgTool_Link, "linklblOldNetPortCfgTool_Link");
            this.linklblOldNetPortCfgTool_Link.Name = "linklblOldNetPortCfgTool_Link";
            this.linklblOldNetPortCfgTool_Link.TabStop = true;
            this.linklblOldNetPortCfgTool_Link.Click += new System.EventHandler(this.linklblOldNetPortCfgTool_LinkClicked);
            // 
            // label164
            // 
            resources.ApplyResources(this.label164, "label164");
            this.label164.ForeColor = System.Drawing.Color.DodgerBlue;
            this.label164.Name = "label164";
            // 
            // label165
            // 
            resources.ApplyResources(this.label165, "label165");
            this.label165.ForeColor = System.Drawing.Color.DodgerBlue;
            this.label165.Name = "label165";
            // 
            // linklblNetPortCfgTool_Link
            // 
            resources.ApplyResources(this.linklblNetPortCfgTool_Link, "linklblNetPortCfgTool_Link");
            this.linklblNetPortCfgTool_Link.Name = "linklblNetPortCfgTool_Link";
            this.linklblNetPortCfgTool_Link.TabStop = true;
            this.linklblNetPortCfgTool_Link.LinkClicked += new System.Windows.Forms.LinkLabelLinkClickedEventHandler(this.linklblNetPortCfgTool_LinkClicked);
            // 
            // lblNetPortCount
            // 
            resources.ApplyResources(this.lblNetPortCount, "lblNetPortCount");
            this.lblNetPortCount.ForeColor = System.Drawing.Color.Black;
            this.lblNetPortCount.Name = "lblNetPortCount";
            // 
            // port_setting_tabcontrol
            // 
            resources.ApplyResources(this.port_setting_tabcontrol, "port_setting_tabcontrol");
            this.port_setting_tabcontrol.Controls.Add(this.net_port_0_tabPage);
            this.port_setting_tabcontrol.Controls.Add(this.net_port_1_tabPage);
            this.port_setting_tabcontrol.Name = "port_setting_tabcontrol";
            this.port_setting_tabcontrol.SelectedIndex = 0;
            // 
            // net_port_0_tabPage
            // 
            resources.ApplyResources(this.net_port_0_tabPage, "net_port_0_tabPage");
            this.net_port_0_tabPage.Controls.Add(this.grbDnsDomain);
            this.net_port_0_tabPage.Controls.Add(this.grbDesIpPort);
            this.net_port_0_tabPage.Controls.Add(this.label203);
            this.net_port_0_tabPage.Controls.Add(this.txtbxPort1_Dnsport);
            this.net_port_0_tabPage.Controls.Add(this.label202);
            this.net_port_0_tabPage.Controls.Add(this.txtbxPort1_DnsIp);
            this.net_port_0_tabPage.Controls.Add(this.label128);
            this.net_port_0_tabPage.Controls.Add(this.txtbxPort1_ReConnectCnt);
            this.net_port_0_tabPage.Controls.Add(this.chkbxPort1_DomainEn);
            this.net_port_0_tabPage.Controls.Add(this.label192);
            this.net_port_0_tabPage.Controls.Add(this.label190);
            this.net_port_0_tabPage.Controls.Add(this.label191);
            this.net_port_0_tabPage.Controls.Add(this.chkbxPort1_ResetCtrl);
            this.net_port_0_tabPage.Controls.Add(this.label189);
            this.net_port_0_tabPage.Controls.Add(this.txtbxPort1_RxTimeout);
            this.net_port_0_tabPage.Controls.Add(this.label188);
            this.net_port_0_tabPage.Controls.Add(this.txtbxPort1_RxPkgLen);
            this.net_port_0_tabPage.Controls.Add(this.label180);
            this.net_port_0_tabPage.Controls.Add(this.chkbxPort1_PhyDisconnect);
            this.net_port_0_tabPage.Controls.Add(this.chkbxPort1_PortEn);
            this.net_port_0_tabPage.Controls.Add(this.chkbxPort1_RandEn);
            this.net_port_0_tabPage.Controls.Add(this.label169);
            this.net_port_0_tabPage.Controls.Add(this.cmbbxPort1_Parity);
            this.net_port_0_tabPage.Controls.Add(this.label168);
            this.net_port_0_tabPage.Controls.Add(this.cmbbxPort1_StopBits);
            this.net_port_0_tabPage.Controls.Add(this.label167);
            this.net_port_0_tabPage.Controls.Add(this.cmbbxPort1_DataSize);
            this.net_port_0_tabPage.Controls.Add(this.label166);
            this.net_port_0_tabPage.Controls.Add(this.cmbbxPort1_BaudRate);
            this.net_port_0_tabPage.Controls.Add(this.txtbxPort1_NetPort);
            this.net_port_0_tabPage.Controls.Add(this.label126);
            this.net_port_0_tabPage.Controls.Add(this.label125);
            this.net_port_0_tabPage.Controls.Add(this.cmbbxPort1_NetMode);
            this.net_port_0_tabPage.Name = "net_port_0_tabPage";
            this.net_port_0_tabPage.UseVisualStyleBackColor = true;
            // 
            // grbDnsDomain
            // 
            resources.ApplyResources(this.grbDnsDomain, "grbDnsDomain");
            this.grbDnsDomain.Controls.Add(this.txtbxPort1_DnsDomain);
            this.grbDnsDomain.Name = "grbDnsDomain";
            this.grbDnsDomain.TabStop = false;
            // 
            // txtbxPort1_DnsDomain
            // 
            resources.ApplyResources(this.txtbxPort1_DnsDomain, "txtbxPort1_DnsDomain");
            this.txtbxPort1_DnsDomain.Name = "txtbxPort1_DnsDomain";
            // 
            // grbDesIpPort
            // 
            resources.ApplyResources(this.grbDesIpPort, "grbDesIpPort");
            this.grbDesIpPort.Controls.Add(this.txtbxPort1_DesIp);
            this.grbDesIpPort.Controls.Add(this.txtbxPort1_DesPort);
            this.grbDesIpPort.Name = "grbDesIpPort";
            this.grbDesIpPort.TabStop = false;
            // 
            // txtbxPort1_DesIp
            // 
            resources.ApplyResources(this.txtbxPort1_DesIp, "txtbxPort1_DesIp");
            this.txtbxPort1_DesIp.Name = "txtbxPort1_DesIp";
            // 
            // txtbxPort1_DesPort
            // 
            resources.ApplyResources(this.txtbxPort1_DesPort, "txtbxPort1_DesPort");
            this.txtbxPort1_DesPort.Name = "txtbxPort1_DesPort";
            // 
            // label203
            // 
            resources.ApplyResources(this.label203, "label203");
            this.label203.Name = "label203";
            // 
            // txtbxPort1_Dnsport
            // 
            resources.ApplyResources(this.txtbxPort1_Dnsport, "txtbxPort1_Dnsport");
            this.txtbxPort1_Dnsport.Name = "txtbxPort1_Dnsport";
            // 
            // label202
            // 
            resources.ApplyResources(this.label202, "label202");
            this.label202.Name = "label202";
            // 
            // txtbxPort1_DnsIp
            // 
            resources.ApplyResources(this.txtbxPort1_DnsIp, "txtbxPort1_DnsIp");
            this.txtbxPort1_DnsIp.Name = "txtbxPort1_DnsIp";
            // 
            // label128
            // 
            resources.ApplyResources(this.label128, "label128");
            this.label128.Name = "label128";
            // 
            // txtbxPort1_ReConnectCnt
            // 
            resources.ApplyResources(this.txtbxPort1_ReConnectCnt, "txtbxPort1_ReConnectCnt");
            this.txtbxPort1_ReConnectCnt.Name = "txtbxPort1_ReConnectCnt";
            // 
            // chkbxPort1_DomainEn
            // 
            resources.ApplyResources(this.chkbxPort1_DomainEn, "chkbxPort1_DomainEn");
            this.chkbxPort1_DomainEn.Name = "chkbxPort1_DomainEn";
            this.chkbxPort1_DomainEn.UseVisualStyleBackColor = true;
            this.chkbxPort1_DomainEn.CheckedChanged += new System.EventHandler(this.chkbxPort1_DomainEn_CheckedChanged);
            // 
            // label192
            // 
            resources.ApplyResources(this.label192, "label192");
            this.label192.Name = "label192";
            // 
            // label190
            // 
            resources.ApplyResources(this.label190, "label190");
            this.label190.Name = "label190";
            // 
            // label191
            // 
            resources.ApplyResources(this.label191, "label191");
            this.label191.Name = "label191";
            // 
            // chkbxPort1_ResetCtrl
            // 
            resources.ApplyResources(this.chkbxPort1_ResetCtrl, "chkbxPort1_ResetCtrl");
            this.chkbxPort1_ResetCtrl.Name = "chkbxPort1_ResetCtrl";
            this.chkbxPort1_ResetCtrl.UseVisualStyleBackColor = true;
            // 
            // label189
            // 
            resources.ApplyResources(this.label189, "label189");
            this.label189.Name = "label189";
            // 
            // txtbxPort1_RxTimeout
            // 
            resources.ApplyResources(this.txtbxPort1_RxTimeout, "txtbxPort1_RxTimeout");
            this.txtbxPort1_RxTimeout.Name = "txtbxPort1_RxTimeout";
            // 
            // label188
            // 
            resources.ApplyResources(this.label188, "label188");
            this.label188.Name = "label188";
            // 
            // txtbxPort1_RxPkgLen
            // 
            resources.ApplyResources(this.txtbxPort1_RxPkgLen, "txtbxPort1_RxPkgLen");
            this.txtbxPort1_RxPkgLen.Name = "txtbxPort1_RxPkgLen";
            // 
            // label180
            // 
            resources.ApplyResources(this.label180, "label180");
            this.label180.Name = "label180";
            // 
            // chkbxPort1_PhyDisconnect
            // 
            resources.ApplyResources(this.chkbxPort1_PhyDisconnect, "chkbxPort1_PhyDisconnect");
            this.chkbxPort1_PhyDisconnect.Name = "chkbxPort1_PhyDisconnect";
            this.chkbxPort1_PhyDisconnect.UseVisualStyleBackColor = true;
            // 
            // chkbxPort1_PortEn
            // 
            resources.ApplyResources(this.chkbxPort1_PortEn, "chkbxPort1_PortEn");
            this.chkbxPort1_PortEn.Name = "chkbxPort1_PortEn";
            this.chkbxPort1_PortEn.UseVisualStyleBackColor = true;
            // 
            // chkbxPort1_RandEn
            // 
            resources.ApplyResources(this.chkbxPort1_RandEn, "chkbxPort1_RandEn");
            this.chkbxPort1_RandEn.Name = "chkbxPort1_RandEn";
            this.chkbxPort1_RandEn.UseVisualStyleBackColor = true;
            this.chkbxPort1_RandEn.CheckedChanged += new System.EventHandler(this.chkbxPort1_RandEn_CheckedChanged);
            // 
            // label169
            // 
            resources.ApplyResources(this.label169, "label169");
            this.label169.Name = "label169";
            // 
            // cmbbxPort1_Parity
            // 
            resources.ApplyResources(this.cmbbxPort1_Parity, "cmbbxPort1_Parity");
            this.cmbbxPort1_Parity.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbbxPort1_Parity.FormattingEnabled = true;
            this.cmbbxPort1_Parity.Name = "cmbbxPort1_Parity";
            // 
            // label168
            // 
            resources.ApplyResources(this.label168, "label168");
            this.label168.Name = "label168";
            // 
            // cmbbxPort1_StopBits
            // 
            resources.ApplyResources(this.cmbbxPort1_StopBits, "cmbbxPort1_StopBits");
            this.cmbbxPort1_StopBits.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbbxPort1_StopBits.FormattingEnabled = true;
            this.cmbbxPort1_StopBits.Name = "cmbbxPort1_StopBits";
            // 
            // label167
            // 
            resources.ApplyResources(this.label167, "label167");
            this.label167.Name = "label167";
            // 
            // cmbbxPort1_DataSize
            // 
            resources.ApplyResources(this.cmbbxPort1_DataSize, "cmbbxPort1_DataSize");
            this.cmbbxPort1_DataSize.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbbxPort1_DataSize.FormattingEnabled = true;
            this.cmbbxPort1_DataSize.Name = "cmbbxPort1_DataSize";
            // 
            // label166
            // 
            resources.ApplyResources(this.label166, "label166");
            this.label166.Name = "label166";
            // 
            // cmbbxPort1_BaudRate
            // 
            resources.ApplyResources(this.cmbbxPort1_BaudRate, "cmbbxPort1_BaudRate");
            this.cmbbxPort1_BaudRate.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbbxPort1_BaudRate.FormattingEnabled = true;
            this.cmbbxPort1_BaudRate.Name = "cmbbxPort1_BaudRate";
            // 
            // txtbxPort1_NetPort
            // 
            resources.ApplyResources(this.txtbxPort1_NetPort, "txtbxPort1_NetPort");
            this.txtbxPort1_NetPort.Name = "txtbxPort1_NetPort";
            // 
            // label126
            // 
            resources.ApplyResources(this.label126, "label126");
            this.label126.Name = "label126";
            // 
            // label125
            // 
            resources.ApplyResources(this.label125, "label125");
            this.label125.Name = "label125";
            // 
            // cmbbxPort1_NetMode
            // 
            resources.ApplyResources(this.cmbbxPort1_NetMode, "cmbbxPort1_NetMode");
            this.cmbbxPort1_NetMode.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbbxPort1_NetMode.FormattingEnabled = true;
            this.cmbbxPort1_NetMode.Name = "cmbbxPort1_NetMode";
            this.cmbbxPort1_NetMode.SelectedIndexChanged += new System.EventHandler(this.cmbbxPort1_NetMode_SelectedIndexChanged);
            // 
            // net_port_1_tabPage
            // 
            resources.ApplyResources(this.net_port_1_tabPage, "net_port_1_tabPage");
            this.net_port_1_tabPage.Controls.Add(this.grbHeartbeat);
            this.net_port_1_tabPage.Controls.Add(this.chkbxPort0PortEn);
            this.net_port_1_tabPage.Name = "net_port_1_tabPage";
            this.net_port_1_tabPage.UseVisualStyleBackColor = true;
            // 
            // grbHeartbeat
            // 
            resources.ApplyResources(this.grbHeartbeat, "grbHeartbeat");
            this.grbHeartbeat.Controls.Add(this.label175);
            this.grbHeartbeat.Controls.Add(this.txtbxHeartbeatContent);
            this.grbHeartbeat.Controls.Add(this.txtbxHeartbeatInterval);
            this.grbHeartbeat.Controls.Add(this.label174);
            this.grbHeartbeat.Name = "grbHeartbeat";
            this.grbHeartbeat.TabStop = false;
            // 
            // label175
            // 
            resources.ApplyResources(this.label175, "label175");
            this.label175.Name = "label175";
            // 
            // txtbxHeartbeatContent
            // 
            resources.ApplyResources(this.txtbxHeartbeatContent, "txtbxHeartbeatContent");
            this.txtbxHeartbeatContent.Name = "txtbxHeartbeatContent";
            // 
            // txtbxHeartbeatInterval
            // 
            resources.ApplyResources(this.txtbxHeartbeatInterval, "txtbxHeartbeatInterval");
            this.txtbxHeartbeatInterval.Name = "txtbxHeartbeatInterval";
            // 
            // label174
            // 
            resources.ApplyResources(this.label174, "label174");
            this.label174.Name = "label174";
            // 
            // chkbxPort0PortEn
            // 
            resources.ApplyResources(this.chkbxPort0PortEn, "chkbxPort0PortEn");
            this.chkbxPort0PortEn.Name = "chkbxPort0PortEn";
            this.chkbxPort0PortEn.UseVisualStyleBackColor = true;
            this.chkbxPort0PortEn.CheckedChanged += new System.EventHandler(this.chkbxPort0PortEn_CheckedChanged);
            // 
            // btnClearNetPort
            // 
            resources.ApplyResources(this.btnClearNetPort, "btnClearNetPort");
            this.btnClearNetPort.Name = "btnClearNetPort";
            this.btnClearNetPort.UseVisualStyleBackColor = true;
            this.btnClearNetPort.Click += new System.EventHandler(this.btnClearNetPort_Click);
            // 
            // net_base_settings_gb
            // 
            resources.ApplyResources(this.net_base_settings_gb, "net_base_settings_gb");
            this.net_base_settings_gb.Controls.Add(this.txtbxHwCfgMac);
            this.net_base_settings_gb.Controls.Add(this.label157);
            this.net_base_settings_gb.Controls.Add(this.label193);
            this.net_base_settings_gb.Controls.Add(this.chkbxHwCfgComCfgEn);
            this.net_base_settings_gb.Controls.Add(this.chkbxHwCfgDhcpEn);
            this.net_base_settings_gb.Controls.Add(this.txtbxHwCfgGateway);
            this.net_base_settings_gb.Controls.Add(this.txtbxHwCfgMask);
            this.net_base_settings_gb.Controls.Add(this.txtbxHwCfgIp);
            this.net_base_settings_gb.Controls.Add(this.txtbxHwCfgDeviceName);
            this.net_base_settings_gb.Controls.Add(this.label161);
            this.net_base_settings_gb.Controls.Add(this.label160);
            this.net_base_settings_gb.Controls.Add(this.label158);
            this.net_base_settings_gb.Controls.Add(this.label156);
            this.net_base_settings_gb.Name = "net_base_settings_gb";
            this.net_base_settings_gb.TabStop = false;
            // 
            // txtbxHwCfgMac
            // 
            resources.ApplyResources(this.txtbxHwCfgMac, "txtbxHwCfgMac");
            this.txtbxHwCfgMac.Name = "txtbxHwCfgMac";
            // 
            // label157
            // 
            resources.ApplyResources(this.label157, "label157");
            this.label157.Name = "label157";
            // 
            // label193
            // 
            resources.ApplyResources(this.label193, "label193");
            this.label193.Name = "label193";
            // 
            // chkbxHwCfgComCfgEn
            // 
            resources.ApplyResources(this.chkbxHwCfgComCfgEn, "chkbxHwCfgComCfgEn");
            this.chkbxHwCfgComCfgEn.Name = "chkbxHwCfgComCfgEn";
            this.chkbxHwCfgComCfgEn.UseVisualStyleBackColor = true;
            // 
            // chkbxHwCfgDhcpEn
            // 
            resources.ApplyResources(this.chkbxHwCfgDhcpEn, "chkbxHwCfgDhcpEn");
            this.chkbxHwCfgDhcpEn.Name = "chkbxHwCfgDhcpEn";
            this.chkbxHwCfgDhcpEn.UseVisualStyleBackColor = true;
            // 
            // txtbxHwCfgGateway
            // 
            resources.ApplyResources(this.txtbxHwCfgGateway, "txtbxHwCfgGateway");
            this.txtbxHwCfgGateway.Name = "txtbxHwCfgGateway";
            // 
            // txtbxHwCfgMask
            // 
            resources.ApplyResources(this.txtbxHwCfgMask, "txtbxHwCfgMask");
            this.txtbxHwCfgMask.Name = "txtbxHwCfgMask";
            // 
            // txtbxHwCfgIp
            // 
            resources.ApplyResources(this.txtbxHwCfgIp, "txtbxHwCfgIp");
            this.txtbxHwCfgIp.Name = "txtbxHwCfgIp";
            // 
            // txtbxHwCfgDeviceName
            // 
            resources.ApplyResources(this.txtbxHwCfgDeviceName, "txtbxHwCfgDeviceName");
            this.txtbxHwCfgDeviceName.Name = "txtbxHwCfgDeviceName";
            // 
            // label161
            // 
            resources.ApplyResources(this.label161, "label161");
            this.label161.Name = "label161";
            // 
            // label160
            // 
            resources.ApplyResources(this.label160, "label160");
            this.label160.Name = "label160";
            // 
            // label158
            // 
            resources.ApplyResources(this.label158, "label158");
            this.label158.Name = "label158";
            // 
            // label156
            // 
            resources.ApplyResources(this.label156, "label156");
            this.label156.Name = "label156";
            // 
            // dgvNetPort
            // 
            resources.ApplyResources(this.dgvNetPort, "dgvNetPort");
            this.dgvNetPort.AllowUserToAddRows = false;
            this.dgvNetPort.ColumnHeadersHeightSizeMode = System.Windows.Forms.DataGridViewColumnHeadersHeightSizeMode.AutoSize;
            this.dgvNetPort.Columns.AddRange(new System.Windows.Forms.DataGridViewColumn[] {
            this.npSerialNumberColumn,
            this.npDeviceNameColumn,
            this.npDeviceIpColumn,
            this.npDeviceMacColumn,
            this.npChipVerColumn,
            this.npPcMacColumn});
            this.dgvNetPort.Name = "dgvNetPort";
            this.dgvNetPort.RowTemplate.Height = 23;
            this.dgvNetPort.SelectionMode = System.Windows.Forms.DataGridViewSelectionMode.FullRowSelect;
            this.dgvNetPort.DoubleClick += new System.EventHandler(this.dgvNetPort_DoubleClick);
            // 
            // npSerialNumberColumn
            // 
            resources.ApplyResources(this.npSerialNumberColumn, "npSerialNumberColumn");
            this.npSerialNumberColumn.Name = "npSerialNumberColumn";
            // 
            // npDeviceNameColumn
            // 
            resources.ApplyResources(this.npDeviceNameColumn, "npDeviceNameColumn");
            this.npDeviceNameColumn.Name = "npDeviceNameColumn";
            this.npDeviceNameColumn.ReadOnly = true;
            // 
            // npDeviceIpColumn
            // 
            resources.ApplyResources(this.npDeviceIpColumn, "npDeviceIpColumn");
            this.npDeviceIpColumn.Name = "npDeviceIpColumn";
            this.npDeviceIpColumn.ReadOnly = true;
            // 
            // npDeviceMacColumn
            // 
            resources.ApplyResources(this.npDeviceMacColumn, "npDeviceMacColumn");
            this.npDeviceMacColumn.Name = "npDeviceMacColumn";
            // 
            // npChipVerColumn
            // 
            resources.ApplyResources(this.npChipVerColumn, "npChipVerColumn");
            this.npChipVerColumn.Name = "npChipVerColumn";
            this.npChipVerColumn.ReadOnly = true;
            // 
            // npPcMacColumn
            // 
            resources.ApplyResources(this.npPcMacColumn, "npPcMacColumn");
            this.npPcMacColumn.Name = "npPcMacColumn";
            // 
            // label159
            // 
            resources.ApplyResources(this.label159, "label159");
            this.label159.Name = "label159";
            // 
            // cmbbxNetCard
            // 
            resources.ApplyResources(this.cmbbxNetCard, "cmbbxNetCard");
            this.cmbbxNetCard.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbbxNetCard.FormattingEnabled = true;
            this.cmbbxNetCard.Name = "cmbbxNetCard";
            this.cmbbxNetCard.SelectedIndexChanged += new System.EventHandler(this.cmbbxNetCard_SelectedIndexChanged);
            // 
            // groupBox30
            // 
            resources.ApplyResources(this.groupBox30, "groupBox30");
            this.groupBox30.Controls.Add(this.lblCurPcMac);
            this.groupBox30.Controls.Add(this.lblCurNetcard);
            this.groupBox30.Name = "groupBox30";
            this.groupBox30.TabStop = false;
            // 
            // lblCurPcMac
            // 
            resources.ApplyResources(this.lblCurPcMac, "lblCurPcMac");
            this.lblCurPcMac.Name = "lblCurPcMac";
            // 
            // lblCurNetcard
            // 
            resources.ApplyResources(this.lblCurNetcard, "lblCurNetcard");
            this.lblCurNetcard.Name = "lblCurNetcard";
            // 
            // btnSearchNetport
            // 
            resources.ApplyResources(this.btnSearchNetport, "btnSearchNetport");
            this.btnSearchNetport.Name = "btnSearchNetport";
            this.btnSearchNetport.UseVisualStyleBackColor = true;
            this.btnSearchNetport.Click += new System.EventHandler(this.btnSearchNetport_Click);
            // 
            // net_refresh_netcard_btn
            // 
            resources.ApplyResources(this.net_refresh_netcard_btn, "net_refresh_netcard_btn");
            this.net_refresh_netcard_btn.Name = "net_refresh_netcard_btn";
            this.net_refresh_netcard_btn.UseVisualStyleBackColor = true;
            this.net_refresh_netcard_btn.Click += new System.EventHandler(this.btnSearchNetCard_Click);
            // 
            // PagSpecialFeature
            // 
            resources.ApplyResources(this.PagSpecialFeature, "PagSpecialFeature");
            this.PagSpecialFeature.BackColor = System.Drawing.Color.WhiteSmoke;
            this.PagSpecialFeature.Controls.Add(this.btn_RefreshSpecial);
            this.PagSpecialFeature.Controls.Add(this.groupBox39);
            this.PagSpecialFeature.Name = "PagSpecialFeature";
            // 
            // btn_RefreshSpecial
            // 
            resources.ApplyResources(this.btn_RefreshSpecial, "btn_RefreshSpecial");
            this.btn_RefreshSpecial.Name = "btn_RefreshSpecial";
            this.btn_RefreshSpecial.UseVisualStyleBackColor = true;
            this.btn_RefreshSpecial.Click += new System.EventHandler(this.btn_RefreshSpecial_Click);
            // 
            // groupBox39
            // 
            resources.ApplyResources(this.groupBox39, "groupBox39");
            this.groupBox39.Controls.Add(this.linkLabel1);
            this.groupBox39.Controls.Add(this.label73);
            this.groupBox39.Controls.Add(this.groupBox40);
            this.groupBox39.Controls.Add(this.cbb_FunctionId);
            this.groupBox39.Controls.Add(this.btn_SetFunction);
            this.groupBox39.Controls.Add(this.btn_GetFunction);
            this.groupBox39.ForeColor = System.Drawing.Color.Black;
            this.groupBox39.Name = "groupBox39";
            this.groupBox39.TabStop = false;
            // 
            // linkLabel1
            // 
            resources.ApplyResources(this.linkLabel1, "linkLabel1");
            this.linkLabel1.LinkColor = System.Drawing.Color.Red;
            this.linkLabel1.Name = "linkLabel1";
            this.linkLabel1.TabStop = true;
            // 
            // label73
            // 
            resources.ApplyResources(this.label73, "label73");
            this.label73.Name = "label73";
            // 
            // groupBox40
            // 
            resources.ApplyResources(this.groupBox40, "groupBox40");
            this.groupBox40.Controls.Add(this.label121);
            this.groupBox40.Controls.Add(this.label122);
            this.groupBox40.Controls.Add(this.txtHStay);
            this.groupBox40.Controls.Add(this.cmbAntSelect8);
            this.groupBox40.Controls.Add(this.label123);
            this.groupBox40.Controls.Add(this.label124);
            this.groupBox40.Controls.Add(this.txtGStay);
            this.groupBox40.Controls.Add(this.cmbAntSelect7);
            this.groupBox40.Controls.Add(this.label127);
            this.groupBox40.Controls.Add(this.label129);
            this.groupBox40.Controls.Add(this.txtFStay);
            this.groupBox40.Controls.Add(this.cmbAntSelect6);
            this.groupBox40.Controls.Add(this.label130);
            this.groupBox40.Controls.Add(this.label131);
            this.groupBox40.Controls.Add(this.txtEStay);
            this.groupBox40.Controls.Add(this.cmbAntSelect5);
            this.groupBox40.Controls.Add(this.tb_Interval);
            this.groupBox40.Controls.Add(this.label84);
            this.groupBox40.Controls.Add(this.btn_GetAntSwitch);
            this.groupBox40.Controls.Add(this.btn_SetAntSwitch);
            this.groupBox40.Controls.Add(this.label93);
            this.groupBox40.Controls.Add(this.label96);
            this.groupBox40.Controls.Add(this.txtDStay);
            this.groupBox40.Controls.Add(this.cmbAntSelect4);
            this.groupBox40.Controls.Add(this.label98);
            this.groupBox40.Controls.Add(this.label116);
            this.groupBox40.Controls.Add(this.txtCStay);
            this.groupBox40.Controls.Add(this.cmbAntSelect3);
            this.groupBox40.Controls.Add(this.label117);
            this.groupBox40.Controls.Add(this.label118);
            this.groupBox40.Controls.Add(this.txtBStay);
            this.groupBox40.Controls.Add(this.cmbAntSelect2);
            this.groupBox40.Controls.Add(this.label119);
            this.groupBox40.Controls.Add(this.label120);
            this.groupBox40.Controls.Add(this.txtAStay);
            this.groupBox40.Controls.Add(this.cmbAntSelect1);
            this.groupBox40.ForeColor = System.Drawing.Color.Black;
            this.groupBox40.Name = "groupBox40";
            this.groupBox40.TabStop = false;
            // 
            // label121
            // 
            resources.ApplyResources(this.label121, "label121");
            this.label121.Name = "label121";
            // 
            // label122
            // 
            resources.ApplyResources(this.label122, "label122");
            this.label122.Name = "label122";
            // 
            // txtHStay
            // 
            resources.ApplyResources(this.txtHStay, "txtHStay");
            this.txtHStay.Name = "txtHStay";
            // 
            // cmbAntSelect8
            // 
            resources.ApplyResources(this.cmbAntSelect8, "cmbAntSelect8");
            this.cmbAntSelect8.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbAntSelect8.FormattingEnabled = true;
            this.cmbAntSelect8.Items.AddRange(new object[] {
            resources.GetString("cmbAntSelect8.Items"),
            resources.GetString("cmbAntSelect8.Items1"),
            resources.GetString("cmbAntSelect8.Items2"),
            resources.GetString("cmbAntSelect8.Items3"),
            resources.GetString("cmbAntSelect8.Items4"),
            resources.GetString("cmbAntSelect8.Items5"),
            resources.GetString("cmbAntSelect8.Items6"),
            resources.GetString("cmbAntSelect8.Items7")});
            this.cmbAntSelect8.Name = "cmbAntSelect8";
            // 
            // label123
            // 
            resources.ApplyResources(this.label123, "label123");
            this.label123.Name = "label123";
            // 
            // label124
            // 
            resources.ApplyResources(this.label124, "label124");
            this.label124.Name = "label124";
            // 
            // txtGStay
            // 
            resources.ApplyResources(this.txtGStay, "txtGStay");
            this.txtGStay.Name = "txtGStay";
            // 
            // cmbAntSelect7
            // 
            resources.ApplyResources(this.cmbAntSelect7, "cmbAntSelect7");
            this.cmbAntSelect7.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbAntSelect7.FormattingEnabled = true;
            this.cmbAntSelect7.Items.AddRange(new object[] {
            resources.GetString("cmbAntSelect7.Items"),
            resources.GetString("cmbAntSelect7.Items1"),
            resources.GetString("cmbAntSelect7.Items2"),
            resources.GetString("cmbAntSelect7.Items3"),
            resources.GetString("cmbAntSelect7.Items4"),
            resources.GetString("cmbAntSelect7.Items5"),
            resources.GetString("cmbAntSelect7.Items6"),
            resources.GetString("cmbAntSelect7.Items7")});
            this.cmbAntSelect7.Name = "cmbAntSelect7";
            // 
            // label127
            // 
            resources.ApplyResources(this.label127, "label127");
            this.label127.Name = "label127";
            // 
            // label129
            // 
            resources.ApplyResources(this.label129, "label129");
            this.label129.Name = "label129";
            // 
            // txtFStay
            // 
            resources.ApplyResources(this.txtFStay, "txtFStay");
            this.txtFStay.Name = "txtFStay";
            // 
            // cmbAntSelect6
            // 
            resources.ApplyResources(this.cmbAntSelect6, "cmbAntSelect6");
            this.cmbAntSelect6.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbAntSelect6.FormattingEnabled = true;
            this.cmbAntSelect6.Items.AddRange(new object[] {
            resources.GetString("cmbAntSelect6.Items"),
            resources.GetString("cmbAntSelect6.Items1"),
            resources.GetString("cmbAntSelect6.Items2"),
            resources.GetString("cmbAntSelect6.Items3"),
            resources.GetString("cmbAntSelect6.Items4"),
            resources.GetString("cmbAntSelect6.Items5"),
            resources.GetString("cmbAntSelect6.Items6"),
            resources.GetString("cmbAntSelect6.Items7")});
            this.cmbAntSelect6.Name = "cmbAntSelect6";
            // 
            // label130
            // 
            resources.ApplyResources(this.label130, "label130");
            this.label130.Name = "label130";
            // 
            // label131
            // 
            resources.ApplyResources(this.label131, "label131");
            this.label131.Name = "label131";
            // 
            // txtEStay
            // 
            resources.ApplyResources(this.txtEStay, "txtEStay");
            this.txtEStay.Name = "txtEStay";
            // 
            // cmbAntSelect5
            // 
            resources.ApplyResources(this.cmbAntSelect5, "cmbAntSelect5");
            this.cmbAntSelect5.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbAntSelect5.FormattingEnabled = true;
            this.cmbAntSelect5.Items.AddRange(new object[] {
            resources.GetString("cmbAntSelect5.Items"),
            resources.GetString("cmbAntSelect5.Items1"),
            resources.GetString("cmbAntSelect5.Items2"),
            resources.GetString("cmbAntSelect5.Items3"),
            resources.GetString("cmbAntSelect5.Items4"),
            resources.GetString("cmbAntSelect5.Items5"),
            resources.GetString("cmbAntSelect5.Items6"),
            resources.GetString("cmbAntSelect5.Items7")});
            this.cmbAntSelect5.Name = "cmbAntSelect5";
            // 
            // tb_Interval
            // 
            resources.ApplyResources(this.tb_Interval, "tb_Interval");
            this.tb_Interval.Name = "tb_Interval";
            // 
            // label84
            // 
            resources.ApplyResources(this.label84, "label84");
            this.label84.ForeColor = System.Drawing.SystemColors.ControlText;
            this.label84.Name = "label84";
            // 
            // btn_GetAntSwitch
            // 
            resources.ApplyResources(this.btn_GetAntSwitch, "btn_GetAntSwitch");
            this.btn_GetAntSwitch.Name = "btn_GetAntSwitch";
            this.btn_GetAntSwitch.UseVisualStyleBackColor = true;
            this.btn_GetAntSwitch.Click += new System.EventHandler(this.btn_GetAntSwitch_Click);
            // 
            // btn_SetAntSwitch
            // 
            resources.ApplyResources(this.btn_SetAntSwitch, "btn_SetAntSwitch");
            this.btn_SetAntSwitch.Name = "btn_SetAntSwitch";
            this.btn_SetAntSwitch.UseVisualStyleBackColor = true;
            this.btn_SetAntSwitch.Click += new System.EventHandler(this.btn_SetAntSwitch_Click);
            // 
            // label93
            // 
            resources.ApplyResources(this.label93, "label93");
            this.label93.Name = "label93";
            // 
            // label96
            // 
            resources.ApplyResources(this.label96, "label96");
            this.label96.Name = "label96";
            // 
            // txtDStay
            // 
            resources.ApplyResources(this.txtDStay, "txtDStay");
            this.txtDStay.Name = "txtDStay";
            // 
            // cmbAntSelect4
            // 
            resources.ApplyResources(this.cmbAntSelect4, "cmbAntSelect4");
            this.cmbAntSelect4.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbAntSelect4.FormattingEnabled = true;
            this.cmbAntSelect4.Items.AddRange(new object[] {
            resources.GetString("cmbAntSelect4.Items"),
            resources.GetString("cmbAntSelect4.Items1"),
            resources.GetString("cmbAntSelect4.Items2"),
            resources.GetString("cmbAntSelect4.Items3"),
            resources.GetString("cmbAntSelect4.Items4"),
            resources.GetString("cmbAntSelect4.Items5"),
            resources.GetString("cmbAntSelect4.Items6"),
            resources.GetString("cmbAntSelect4.Items7")});
            this.cmbAntSelect4.Name = "cmbAntSelect4";
            // 
            // label98
            // 
            resources.ApplyResources(this.label98, "label98");
            this.label98.Name = "label98";
            // 
            // label116
            // 
            resources.ApplyResources(this.label116, "label116");
            this.label116.Name = "label116";
            // 
            // txtCStay
            // 
            resources.ApplyResources(this.txtCStay, "txtCStay");
            this.txtCStay.Name = "txtCStay";
            // 
            // cmbAntSelect3
            // 
            resources.ApplyResources(this.cmbAntSelect3, "cmbAntSelect3");
            this.cmbAntSelect3.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbAntSelect3.FormattingEnabled = true;
            this.cmbAntSelect3.Items.AddRange(new object[] {
            resources.GetString("cmbAntSelect3.Items"),
            resources.GetString("cmbAntSelect3.Items1"),
            resources.GetString("cmbAntSelect3.Items2"),
            resources.GetString("cmbAntSelect3.Items3"),
            resources.GetString("cmbAntSelect3.Items4"),
            resources.GetString("cmbAntSelect3.Items5"),
            resources.GetString("cmbAntSelect3.Items6"),
            resources.GetString("cmbAntSelect3.Items7")});
            this.cmbAntSelect3.Name = "cmbAntSelect3";
            // 
            // label117
            // 
            resources.ApplyResources(this.label117, "label117");
            this.label117.Name = "label117";
            // 
            // label118
            // 
            resources.ApplyResources(this.label118, "label118");
            this.label118.Name = "label118";
            // 
            // txtBStay
            // 
            resources.ApplyResources(this.txtBStay, "txtBStay");
            this.txtBStay.Name = "txtBStay";
            // 
            // cmbAntSelect2
            // 
            resources.ApplyResources(this.cmbAntSelect2, "cmbAntSelect2");
            this.cmbAntSelect2.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbAntSelect2.FormattingEnabled = true;
            this.cmbAntSelect2.Items.AddRange(new object[] {
            resources.GetString("cmbAntSelect2.Items"),
            resources.GetString("cmbAntSelect2.Items1"),
            resources.GetString("cmbAntSelect2.Items2"),
            resources.GetString("cmbAntSelect2.Items3"),
            resources.GetString("cmbAntSelect2.Items4"),
            resources.GetString("cmbAntSelect2.Items5"),
            resources.GetString("cmbAntSelect2.Items6"),
            resources.GetString("cmbAntSelect2.Items7")});
            this.cmbAntSelect2.Name = "cmbAntSelect2";
            // 
            // label119
            // 
            resources.ApplyResources(this.label119, "label119");
            this.label119.Name = "label119";
            // 
            // label120
            // 
            resources.ApplyResources(this.label120, "label120");
            this.label120.Name = "label120";
            // 
            // txtAStay
            // 
            resources.ApplyResources(this.txtAStay, "txtAStay");
            this.txtAStay.Name = "txtAStay";
            // 
            // cmbAntSelect1
            // 
            resources.ApplyResources(this.cmbAntSelect1, "cmbAntSelect1");
            this.cmbAntSelect1.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cmbAntSelect1.FormattingEnabled = true;
            this.cmbAntSelect1.Items.AddRange(new object[] {
            resources.GetString("cmbAntSelect1.Items"),
            resources.GetString("cmbAntSelect1.Items1"),
            resources.GetString("cmbAntSelect1.Items2"),
            resources.GetString("cmbAntSelect1.Items3"),
            resources.GetString("cmbAntSelect1.Items4"),
            resources.GetString("cmbAntSelect1.Items5"),
            resources.GetString("cmbAntSelect1.Items6"),
            resources.GetString("cmbAntSelect1.Items7")});
            this.cmbAntSelect1.Name = "cmbAntSelect1";
            // 
            // cbb_FunctionId
            // 
            resources.ApplyResources(this.cbb_FunctionId, "cbb_FunctionId");
            this.cbb_FunctionId.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.cbb_FunctionId.ForeColor = System.Drawing.SystemColors.WindowFrame;
            this.cbb_FunctionId.FormattingEnabled = true;
            this.cbb_FunctionId.Items.AddRange(new object[] {
            resources.GetString("cbb_FunctionId.Items"),
            resources.GetString("cbb_FunctionId.Items1"),
            resources.GetString("cbb_FunctionId.Items2"),
            resources.GetString("cbb_FunctionId.Items3"),
            resources.GetString("cbb_FunctionId.Items4"),
            resources.GetString("cbb_FunctionId.Items5"),
            resources.GetString("cbb_FunctionId.Items6"),
            resources.GetString("cbb_FunctionId.Items7"),
            resources.GetString("cbb_FunctionId.Items8"),
            resources.GetString("cbb_FunctionId.Items9"),
            resources.GetString("cbb_FunctionId.Items10"),
            resources.GetString("cbb_FunctionId.Items11"),
            resources.GetString("cbb_FunctionId.Items12"),
            resources.GetString("cbb_FunctionId.Items13"),
            resources.GetString("cbb_FunctionId.Items14"),
            resources.GetString("cbb_FunctionId.Items15"),
            resources.GetString("cbb_FunctionId.Items16"),
            resources.GetString("cbb_FunctionId.Items17"),
            resources.GetString("cbb_FunctionId.Items18"),
            resources.GetString("cbb_FunctionId.Items19"),
            resources.GetString("cbb_FunctionId.Items20"),
            resources.GetString("cbb_FunctionId.Items21"),
            resources.GetString("cbb_FunctionId.Items22"),
            resources.GetString("cbb_FunctionId.Items23"),
            resources.GetString("cbb_FunctionId.Items24"),
            resources.GetString("cbb_FunctionId.Items25"),
            resources.GetString("cbb_FunctionId.Items26"),
            resources.GetString("cbb_FunctionId.Items27"),
            resources.GetString("cbb_FunctionId.Items28"),
            resources.GetString("cbb_FunctionId.Items29"),
            resources.GetString("cbb_FunctionId.Items30"),
            resources.GetString("cbb_FunctionId.Items31"),
            resources.GetString("cbb_FunctionId.Items32"),
            resources.GetString("cbb_FunctionId.Items33"),
            resources.GetString("cbb_FunctionId.Items34"),
            resources.GetString("cbb_FunctionId.Items35"),
            resources.GetString("cbb_FunctionId.Items36"),
            resources.GetString("cbb_FunctionId.Items37"),
            resources.GetString("cbb_FunctionId.Items38"),
            resources.GetString("cbb_FunctionId.Items39"),
            resources.GetString("cbb_FunctionId.Items40"),
            resources.GetString("cbb_FunctionId.Items41"),
            resources.GetString("cbb_FunctionId.Items42"),
            resources.GetString("cbb_FunctionId.Items43"),
            resources.GetString("cbb_FunctionId.Items44"),
            resources.GetString("cbb_FunctionId.Items45"),
            resources.GetString("cbb_FunctionId.Items46"),
            resources.GetString("cbb_FunctionId.Items47"),
            resources.GetString("cbb_FunctionId.Items48")});
            this.cbb_FunctionId.Name = "cbb_FunctionId";
            // 
            // btn_SetFunction
            // 
            resources.ApplyResources(this.btn_SetFunction, "btn_SetFunction");
            this.btn_SetFunction.Name = "btn_SetFunction";
            this.btn_SetFunction.UseVisualStyleBackColor = true;
            this.btn_SetFunction.Click += new System.EventHandler(this.btn_SetFunction_Click);
            // 
            // btn_GetFunction
            // 
            resources.ApplyResources(this.btn_GetFunction, "btn_GetFunction");
            this.btn_GetFunction.Name = "btn_GetFunction";
            this.btn_GetFunction.UseVisualStyleBackColor = true;
            this.btn_GetFunction.Click += new System.EventHandler(this.btn_GetFunction_Click);
            // 
            // label35
            // 
            resources.ApplyResources(this.label35, "label35");
            this.label35.Name = "label35";
            // 
            // ckDisplayLog
            // 
            resources.ApplyResources(this.ckDisplayLog, "ckDisplayLog");
            this.ckDisplayLog.ForeColor = System.Drawing.Color.Indigo;
            this.ckDisplayLog.Name = "ckDisplayLog";
            this.ckDisplayLog.UseVisualStyleBackColor = true;
            this.ckDisplayLog.CheckedChanged += new System.EventHandler(this.ckDisplayLog_CheckedChanged);
            // 
            // tableLayoutPanel3
            // 
            resources.ApplyResources(this.tableLayoutPanel3, "tableLayoutPanel3");
            this.tableLayoutPanel3.BackColor = System.Drawing.SystemColors.ActiveCaptionText;
            this.tableLayoutPanel3.Controls.Add(this.panel6, 0, 0);
            this.tableLayoutPanel3.Controls.Add(this.panel7, 1, 0);
            this.tableLayoutPanel3.Name = "tableLayoutPanel3";
            // 
            // panel6
            // 
            resources.ApplyResources(this.panel6, "panel6");
            this.panel6.Controls.Add(this.button4);
            this.panel6.Name = "panel6";
            // 
            // button4
            // 
            resources.ApplyResources(this.button4, "button4");
            this.button4.ForeColor = System.Drawing.SystemColors.Desktop;
            this.button4.Name = "button4";
            this.button4.UseVisualStyleBackColor = true;
            // 
            // panel7
            // 
            resources.ApplyResources(this.panel7, "panel7");
            this.panel7.Controls.Add(this.checkBox5);
            this.panel7.Controls.Add(this.checkBox6);
            this.panel7.Controls.Add(this.checkBox7);
            this.panel7.Controls.Add(this.checkBox8);
            this.panel7.Name = "panel7";
            // 
            // checkBox5
            // 
            resources.ApplyResources(this.checkBox5, "checkBox5");
            this.checkBox5.Checked = true;
            this.checkBox5.CheckState = System.Windows.Forms.CheckState.Checked;
            this.checkBox5.Name = "checkBox5";
            this.checkBox5.UseVisualStyleBackColor = true;
            // 
            // checkBox6
            // 
            resources.ApplyResources(this.checkBox6, "checkBox6");
            this.checkBox6.Name = "checkBox6";
            this.checkBox6.UseVisualStyleBackColor = true;
            // 
            // checkBox7
            // 
            resources.ApplyResources(this.checkBox7, "checkBox7");
            this.checkBox7.Name = "checkBox7";
            this.checkBox7.UseVisualStyleBackColor = true;
            // 
            // checkBox8
            // 
            resources.ApplyResources(this.checkBox8, "checkBox8");
            this.checkBox8.Name = "checkBox8";
            this.checkBox8.UseVisualStyleBackColor = true;
            // 
            // textBox5
            // 
            resources.ApplyResources(this.textBox5, "textBox5");
            this.textBox5.Name = "textBox5";
            // 
            // textBox6
            // 
            resources.ApplyResources(this.textBox6, "textBox6");
            this.textBox6.Name = "textBox6";
            // 
            // button5
            // 
            resources.ApplyResources(this.button5, "button5");
            this.button5.ForeColor = System.Drawing.SystemColors.Desktop;
            this.button5.Name = "button5";
            this.button5.UseVisualStyleBackColor = true;
            // 
            // label76
            // 
            resources.ApplyResources(this.label76, "label76");
            this.label76.ForeColor = System.Drawing.SystemColors.ControlText;
            this.label76.Name = "label76";
            // 
            // label77
            // 
            resources.ApplyResources(this.label77, "label77");
            this.label77.ForeColor = System.Drawing.SystemColors.ControlText;
            this.label77.Name = "label77";
            // 
            // label78
            // 
            resources.ApplyResources(this.label78, "label78");
            this.label78.ForeColor = System.Drawing.SystemColors.Desktop;
            this.label78.Name = "label78";
            // 
            // groupBox8
            // 
            resources.ApplyResources(this.groupBox8, "groupBox8");
            this.groupBox8.Controls.Add(this.comboBox9);
            this.groupBox8.Controls.Add(this.ledControl9);
            this.groupBox8.Controls.Add(this.ledControl10);
            this.groupBox8.Controls.Add(this.ledControl11);
            this.groupBox8.Controls.Add(this.ledControl12);
            this.groupBox8.Controls.Add(this.label79);
            this.groupBox8.Controls.Add(this.label80);
            this.groupBox8.Controls.Add(this.label81);
            this.groupBox8.Controls.Add(this.label82);
            this.groupBox8.Controls.Add(this.label83);
            this.groupBox8.Controls.Add(this.ledControl13);
            this.groupBox8.ForeColor = System.Drawing.SystemColors.ControlText;
            this.groupBox8.Name = "groupBox8";
            this.groupBox8.TabStop = false;
            // 
            // comboBox9
            // 
            resources.ApplyResources(this.comboBox9, "comboBox9");
            this.comboBox9.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.comboBox9.ForeColor = System.Drawing.SystemColors.InfoText;
            this.comboBox9.FormattingEnabled = true;
            this.comboBox9.Items.AddRange(new object[] {
            resources.GetString("comboBox9.Items"),
            resources.GetString("comboBox9.Items1"),
            resources.GetString("comboBox9.Items2"),
            resources.GetString("comboBox9.Items3"),
            resources.GetString("comboBox9.Items4")});
            this.comboBox9.Name = "comboBox9";
            // 
            // ledControl9
            // 
            resources.ApplyResources(this.ledControl9, "ledControl9");
            this.ledControl9.BackColor = System.Drawing.Color.Transparent;
            this.ledControl9.BackColor_1 = System.Drawing.Color.Transparent;
            this.ledControl9.BackColor_2 = System.Drawing.Color.DarkRed;
            this.ledControl9.BevelRate = 0.1F;
            this.ledControl9.BorderColor = System.Drawing.Color.Lavender;
            this.ledControl9.FadedColor = System.Drawing.SystemColors.ControlLight;
            this.ledControl9.FocusedBorderColor = System.Drawing.Color.LightCoral;
            this.ledControl9.ForeColor = System.Drawing.Color.Black;
            this.ledControl9.HighlightOpaque = ((byte)(20));
            this.ledControl9.Name = "ledControl9";
            this.ledControl9.RoundCorner = true;
            this.ledControl9.SegmentIntervalRatio = 50;
            this.ledControl9.ShowHighlight = true;
            this.ledControl9.TextAlignment = Led.Alignment.Right;
            this.ledControl9.TotalCharCount = 10;
            // 
            // ledControl10
            // 
            resources.ApplyResources(this.ledControl10, "ledControl10");
            this.ledControl10.BackColor = System.Drawing.Color.Transparent;
            this.ledControl10.BackColor_1 = System.Drawing.Color.Transparent;
            this.ledControl10.BackColor_2 = System.Drawing.Color.DarkRed;
            this.ledControl10.BevelRate = 0.1F;
            this.ledControl10.BorderColor = System.Drawing.Color.Lavender;
            this.ledControl10.FadedColor = System.Drawing.SystemColors.ControlLight;
            this.ledControl10.FocusedBorderColor = System.Drawing.Color.LightCoral;
            this.ledControl10.ForeColor = System.Drawing.Color.Black;
            this.ledControl10.HighlightOpaque = ((byte)(20));
            this.ledControl10.Name = "ledControl10";
            this.ledControl10.RoundCorner = true;
            this.ledControl10.SegmentIntervalRatio = 50;
            this.ledControl10.ShowHighlight = true;
            this.ledControl10.TextAlignment = Led.Alignment.Right;
            // 
            // ledControl11
            // 
            resources.ApplyResources(this.ledControl11, "ledControl11");
            this.ledControl11.BackColor = System.Drawing.Color.Transparent;
            this.ledControl11.BackColor_1 = System.Drawing.Color.Transparent;
            this.ledControl11.BackColor_2 = System.Drawing.Color.DarkRed;
            this.ledControl11.BevelRate = 0.1F;
            this.ledControl11.BorderColor = System.Drawing.Color.Lavender;
            this.ledControl11.FadedColor = System.Drawing.SystemColors.ControlLight;
            this.ledControl11.FocusedBorderColor = System.Drawing.Color.LightCoral;
            this.ledControl11.ForeColor = System.Drawing.Color.Black;
            this.ledControl11.HighlightOpaque = ((byte)(20));
            this.ledControl11.Name = "ledControl11";
            this.ledControl11.RoundCorner = true;
            this.ledControl11.SegmentIntervalRatio = 50;
            this.ledControl11.ShowHighlight = true;
            this.ledControl11.TextAlignment = Led.Alignment.Right;
            // 
            // ledControl12
            // 
            resources.ApplyResources(this.ledControl12, "ledControl12");
            this.ledControl12.BackColor = System.Drawing.Color.Transparent;
            this.ledControl12.BackColor_1 = System.Drawing.Color.Transparent;
            this.ledControl12.BackColor_2 = System.Drawing.Color.DarkRed;
            this.ledControl12.BevelRate = 0.1F;
            this.ledControl12.BorderColor = System.Drawing.Color.Lavender;
            this.ledControl12.FadedColor = System.Drawing.SystemColors.ControlLight;
            this.ledControl12.FocusedBorderColor = System.Drawing.Color.LightCoral;
            this.ledControl12.ForeColor = System.Drawing.Color.Black;
            this.ledControl12.HighlightOpaque = ((byte)(20));
            this.ledControl12.Name = "ledControl12";
            this.ledControl12.RoundCorner = true;
            this.ledControl12.SegmentIntervalRatio = 50;
            this.ledControl12.ShowHighlight = true;
            this.ledControl12.TextAlignment = Led.Alignment.Right;
            // 
            // label79
            // 
            resources.ApplyResources(this.label79, "label79");
            this.label79.ForeColor = System.Drawing.SystemColors.Desktop;
            this.label79.Name = "label79";
            // 
            // label80
            // 
            resources.ApplyResources(this.label80, "label80");
            this.label80.ForeColor = System.Drawing.SystemColors.Desktop;
            this.label80.Name = "label80";
            // 
            // label81
            // 
            resources.ApplyResources(this.label81, "label81");
            this.label81.ForeColor = System.Drawing.SystemColors.Desktop;
            this.label81.Name = "label81";
            // 
            // label82
            // 
            resources.ApplyResources(this.label82, "label82");
            this.label82.ForeColor = System.Drawing.SystemColors.Desktop;
            this.label82.Name = "label82";
            // 
            // label83
            // 
            resources.ApplyResources(this.label83, "label83");
            this.label83.ForeColor = System.Drawing.SystemColors.ControlText;
            this.label83.Name = "label83";
            // 
            // ledControl13
            // 
            resources.ApplyResources(this.ledControl13, "ledControl13");
            this.ledControl13.BackColor = System.Drawing.Color.Transparent;
            this.ledControl13.BackColor_1 = System.Drawing.Color.Transparent;
            this.ledControl13.BackColor_2 = System.Drawing.Color.DarkRed;
            this.ledControl13.BevelRate = 0.1F;
            this.ledControl13.BorderColor = System.Drawing.Color.Lavender;
            this.ledControl13.FadedColor = System.Drawing.SystemColors.ControlLight;
            this.ledControl13.FocusedBorderColor = System.Drawing.Color.LightCoral;
            this.ledControl13.ForeColor = System.Drawing.Color.Purple;
            this.ledControl13.HighlightOpaque = ((byte)(20));
            this.ledControl13.Name = "ledControl13";
            this.ledControl13.RoundCorner = true;
            this.ledControl13.SegmentIntervalRatio = 50;
            this.ledControl13.ShowHighlight = true;
            this.ledControl13.TextAlignment = Led.Alignment.Right;
            // 
            // listView1
            // 
            resources.ApplyResources(this.listView1, "listView1");
            this.listView1.Columns.AddRange(new System.Windows.Forms.ColumnHeader[] {
            this.columnHeader43,
            this.columnHeader44,
            this.columnHeader45,
            this.columnHeader46,
            this.columnHeader47,
            this.columnHeader48});
            this.listView1.HideSelection = false;
            this.listView1.Name = "listView1";
            this.listView1.UseCompatibleStateImageBehavior = false;
            this.listView1.View = System.Windows.Forms.View.Details;
            // 
            // columnHeader43
            // 
            resources.ApplyResources(this.columnHeader43, "columnHeader43");
            // 
            // columnHeader44
            // 
            resources.ApplyResources(this.columnHeader44, "columnHeader44");
            // 
            // columnHeader45
            // 
            resources.ApplyResources(this.columnHeader45, "columnHeader45");
            // 
            // columnHeader46
            // 
            resources.ApplyResources(this.columnHeader46, "columnHeader46");
            // 
            // columnHeader47
            // 
            resources.ApplyResources(this.columnHeader47, "columnHeader47");
            // 
            // columnHeader48
            // 
            resources.ApplyResources(this.columnHeader48, "columnHeader48");
            // 
            // comboBox10
            // 
            resources.ApplyResources(this.comboBox10, "comboBox10");
            this.comboBox10.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.comboBox10.ForeColor = System.Drawing.SystemColors.InfoText;
            this.comboBox10.FormattingEnabled = true;
            this.comboBox10.Items.AddRange(new object[] {
            resources.GetString("comboBox10.Items"),
            resources.GetString("comboBox10.Items1"),
            resources.GetString("comboBox10.Items2"),
            resources.GetString("comboBox10.Items3"),
            resources.GetString("comboBox10.Items4")});
            this.comboBox10.Name = "comboBox10";
            // 
            // label87
            // 
            resources.ApplyResources(this.label87, "label87");
            this.label87.ForeColor = System.Drawing.SystemColors.Desktop;
            this.label87.Name = "label87";
            // 
            // label88
            // 
            resources.ApplyResources(this.label88, "label88");
            this.label88.ForeColor = System.Drawing.SystemColors.Desktop;
            this.label88.Name = "label88";
            // 
            // label89
            // 
            resources.ApplyResources(this.label89, "label89");
            this.label89.ForeColor = System.Drawing.SystemColors.Desktop;
            this.label89.Name = "label89";
            // 
            // label90
            // 
            resources.ApplyResources(this.label90, "label90");
            this.label90.ForeColor = System.Drawing.SystemColors.Desktop;
            this.label90.Name = "label90";
            // 
            // label91
            // 
            resources.ApplyResources(this.label91, "label91");
            this.label91.ForeColor = System.Drawing.SystemColors.ControlText;
            this.label91.Name = "label91";
            // 
            // ckClearOperationRec
            // 
            resources.ApplyResources(this.ckClearOperationRec, "ckClearOperationRec");
            this.ckClearOperationRec.Checked = true;
            this.ckClearOperationRec.CheckState = System.Windows.Forms.CheckState.Checked;
            this.ckClearOperationRec.Name = "ckClearOperationRec";
            this.ckClearOperationRec.UseVisualStyleBackColor = true;
            // 
            // panel1
            // 
            resources.ApplyResources(this.panel1, "panel1");
            this.panel1.Controls.Add(this.ckClearOperationRec);
            this.panel1.Controls.Add(this.lrtxtLog);
            this.panel1.Controls.Add(this.ckDisplayLog);
            this.panel1.Controls.Add(this.label35);
            this.panel1.Name = "panel1";
            // 
            // lrtxtLog
            // 
            resources.ApplyResources(this.lrtxtLog, "lrtxtLog");
            this.lrtxtLog.Name = "lrtxtLog";
            this.lrtxtLog.DoubleClick += new System.EventHandler(this.lrtxtLog_DoubleClick);
            // 
            // ledControl14
            // 
            resources.ApplyResources(this.ledControl14, "ledControl14");
            this.ledControl14.BackColor = System.Drawing.Color.Transparent;
            this.ledControl14.BackColor_1 = System.Drawing.Color.Transparent;
            this.ledControl14.BackColor_2 = System.Drawing.Color.DarkRed;
            this.ledControl14.BevelRate = 0.1F;
            this.ledControl14.BorderColor = System.Drawing.Color.Lavender;
            this.ledControl14.FadedColor = System.Drawing.SystemColors.ControlLight;
            this.ledControl14.FocusedBorderColor = System.Drawing.Color.LightCoral;
            this.ledControl14.ForeColor = System.Drawing.Color.Black;
            this.ledControl14.HighlightOpaque = ((byte)(20));
            this.ledControl14.Name = "ledControl14";
            this.ledControl14.RoundCorner = true;
            this.ledControl14.SegmentIntervalRatio = 50;
            this.ledControl14.ShowHighlight = true;
            this.ledControl14.TextAlignment = Led.Alignment.Right;
            this.ledControl14.TotalCharCount = 10;
            // 
            // ledControl15
            // 
            resources.ApplyResources(this.ledControl15, "ledControl15");
            this.ledControl15.BackColor = System.Drawing.Color.Transparent;
            this.ledControl15.BackColor_1 = System.Drawing.Color.Transparent;
            this.ledControl15.BackColor_2 = System.Drawing.Color.DarkRed;
            this.ledControl15.BevelRate = 0.1F;
            this.ledControl15.BorderColor = System.Drawing.Color.Lavender;
            this.ledControl15.FadedColor = System.Drawing.SystemColors.ControlLight;
            this.ledControl15.FocusedBorderColor = System.Drawing.Color.LightCoral;
            this.ledControl15.ForeColor = System.Drawing.Color.Black;
            this.ledControl15.HighlightOpaque = ((byte)(20));
            this.ledControl15.Name = "ledControl15";
            this.ledControl15.RoundCorner = true;
            this.ledControl15.SegmentIntervalRatio = 50;
            this.ledControl15.ShowHighlight = true;
            this.ledControl15.TextAlignment = Led.Alignment.Right;
            // 
            // ledControl16
            // 
            resources.ApplyResources(this.ledControl16, "ledControl16");
            this.ledControl16.BackColor = System.Drawing.Color.Transparent;
            this.ledControl16.BackColor_1 = System.Drawing.Color.Transparent;
            this.ledControl16.BackColor_2 = System.Drawing.Color.DarkRed;
            this.ledControl16.BevelRate = 0.1F;
            this.ledControl16.BorderColor = System.Drawing.Color.Lavender;
            this.ledControl16.FadedColor = System.Drawing.SystemColors.ControlLight;
            this.ledControl16.FocusedBorderColor = System.Drawing.Color.LightCoral;
            this.ledControl16.ForeColor = System.Drawing.Color.Black;
            this.ledControl16.HighlightOpaque = ((byte)(20));
            this.ledControl16.Name = "ledControl16";
            this.ledControl16.RoundCorner = true;
            this.ledControl16.SegmentIntervalRatio = 50;
            this.ledControl16.ShowHighlight = true;
            this.ledControl16.TextAlignment = Led.Alignment.Right;
            // 
            // ledControl17
            // 
            resources.ApplyResources(this.ledControl17, "ledControl17");
            this.ledControl17.BackColor = System.Drawing.Color.Transparent;
            this.ledControl17.BackColor_1 = System.Drawing.Color.Transparent;
            this.ledControl17.BackColor_2 = System.Drawing.Color.DarkRed;
            this.ledControl17.BevelRate = 0.1F;
            this.ledControl17.BorderColor = System.Drawing.Color.Lavender;
            this.ledControl17.FadedColor = System.Drawing.SystemColors.ControlLight;
            this.ledControl17.FocusedBorderColor = System.Drawing.Color.LightCoral;
            this.ledControl17.ForeColor = System.Drawing.Color.Black;
            this.ledControl17.HighlightOpaque = ((byte)(20));
            this.ledControl17.Name = "ledControl17";
            this.ledControl17.RoundCorner = true;
            this.ledControl17.SegmentIntervalRatio = 50;
            this.ledControl17.ShowHighlight = true;
            this.ledControl17.TextAlignment = Led.Alignment.Right;
            // 
            // ledControl18
            // 
            resources.ApplyResources(this.ledControl18, "ledControl18");
            this.ledControl18.BackColor = System.Drawing.Color.Transparent;
            this.ledControl18.BackColor_1 = System.Drawing.Color.Transparent;
            this.ledControl18.BackColor_2 = System.Drawing.Color.DarkRed;
            this.ledControl18.BevelRate = 0.1F;
            this.ledControl18.BorderColor = System.Drawing.Color.Lavender;
            this.ledControl18.FadedColor = System.Drawing.SystemColors.ControlLight;
            this.ledControl18.FocusedBorderColor = System.Drawing.Color.LightCoral;
            this.ledControl18.ForeColor = System.Drawing.Color.Purple;
            this.ledControl18.HighlightOpaque = ((byte)(20));
            this.ledControl18.Name = "ledControl18";
            this.ledControl18.RoundCorner = true;
            this.ledControl18.SegmentIntervalRatio = 50;
            this.ledControl18.ShowHighlight = true;
            this.ledControl18.TextAlignment = Led.Alignment.Right;
            // 
            // UHFDemo
            // 
            resources.ApplyResources(this, "$this");
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.None;
            this.BackColor = System.Drawing.Color.WhiteSmoke;
            this.Controls.Add(this.panel1);
            this.Controls.Add(this.tabCtrMain);
            this.ForeColor = System.Drawing.Color.Black;
            this.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedSingle;
            this.Name = "UHFDemo";
            this.FormClosing += new System.Windows.Forms.FormClosingEventHandler(this.R2000UartDemo_FormClosing);
            this.Load += new System.EventHandler(this.R2000UartDemo_Load);
            this.tabCtrMain.ResumeLayout(false);
            this.PagReaderSetting.ResumeLayout(false);
            this.tabControl_baseSettings.ResumeLayout(false);
            this.tabPage1.ResumeLayout(false);
            this.flowLayoutPanel2.ResumeLayout(false);
            this.gbModel.ResumeLayout(false);
            this.gbModel.PerformLayout();
            this.groupBox1.ResumeLayout(false);
            this.groupBox24.ResumeLayout(false);
            this.groupBox24.PerformLayout();
            this.gbConnectType.ResumeLayout(false);
            this.gbConnectType.PerformLayout();
            this.grb_rs232.ResumeLayout(false);
            this.grb_rs232.PerformLayout();
            this.grbModuleBaudRate.ResumeLayout(false);
            this.grb_tcp.ResumeLayout(false);
            this.grb_tcp.PerformLayout();
            this.gbCmdReaderAddress.ResumeLayout(false);
            this.gbCmdReaderAddress.PerformLayout();
            this.gbCmdBaudrate.ResumeLayout(false);
            this.gbCmdBaudrate.PerformLayout();
            this.gbCmdReadGpio.ResumeLayout(false);
            this.groupBox11.ResumeLayout(false);
            this.groupBox6.ResumeLayout(false);
            this.groupBox6.PerformLayout();
            this.groupBox7.ResumeLayout(false);
            this.groupBox7.PerformLayout();
            this.groupBox10.ResumeLayout(false);
            this.groupBox4.ResumeLayout(false);
            this.groupBox4.PerformLayout();
            this.groupBox5.ResumeLayout(false);
            this.groupBox5.PerformLayout();
            this.gbCmdBeeper.ResumeLayout(false);
            this.gbCmdTemperature.ResumeLayout(false);
            this.gbCmdTemperature.PerformLayout();
            this.gbCmdVersion.ResumeLayout(false);
            this.gbCmdVersion.PerformLayout();
            this.tabPage2.ResumeLayout(false);
            this.flowLayoutPanel3.ResumeLayout(false);
            this.gbCmdRegion.ResumeLayout(false);
            this.gbCmdRegion.PerformLayout();
            this.groupBox23.ResumeLayout(false);
            this.groupBox23.PerformLayout();
            this.groupBox21.ResumeLayout(false);
            this.groupBox21.PerformLayout();
            this.gbProfile.ResumeLayout(false);
            this.gbProfile.PerformLayout();
            this.gbReturnLoss.ResumeLayout(false);
            this.gbReturnLoss.PerformLayout();
            this.gbMonza.ResumeLayout(false);
            this.gbMonza.PerformLayout();
            this.gbCmdAntDetector.ResumeLayout(false);
            this.gbCmdAntDetector.PerformLayout();
            this.gbCmdAntenna.ResumeLayout(false);
            this.gbCmdAntenna.PerformLayout();
            this.gbCmdOutputPower.ResumeLayout(false);
            this.gbCmdOutputPower.PerformLayout();
            this.tabPage4.ResumeLayout(false);
            this.flowLayoutPanel4.ResumeLayout(false);
            this.gbRfLink.ResumeLayout(false);
            this.gbRfLink.PerformLayout();
            this.grpbQ.ResumeLayout(false);
            this.groupBox34.ResumeLayout(false);
            this.groupBox34.PerformLayout();
            this.groupBox33.ResumeLayout(false);
            this.groupBox33.PerformLayout();
            this.groupBox32.ResumeLayout(false);
            this.groupBox36.ResumeLayout(false);
            this.groupBox38.ResumeLayout(false);
            this.groupBox38.PerformLayout();
            this.groupBox37.ResumeLayout(false);
            this.groupBox37.PerformLayout();
            this.groupBox35.ResumeLayout(false);
            this.groupBox35.PerformLayout();
            this.tabPage5.ResumeLayout(false);
            this.groupBox29.ResumeLayout(false);
            this.groupBox29.PerformLayout();
            this.pageEpcTest.ResumeLayout(false);
            this.tab_6c_Tags_Test.ResumeLayout(false);
            this.pageFast4AntMode.ResumeLayout(false);
            this.pageFast4AntMode.PerformLayout();
            this.panel2.ResumeLayout(false);
            this.panel2.PerformLayout();
            this.flowLayoutPanel1.ResumeLayout(false);
            this.grb_inventory_cfg.ResumeLayout(false);
            this.grb_inventory_cfg.PerformLayout();
            this.grb_Interval.ResumeLayout(false);
            this.grb_Interval.PerformLayout();
            this.grb_Reserve.ResumeLayout(false);
            this.grb_Reserve.PerformLayout();
            this.grb_selectFlags.ResumeLayout(false);
            this.grb_selectFlags.PerformLayout();
            this.grb_sessions.ResumeLayout(false);
            this.grb_sessions.PerformLayout();
            this.grb_targets.ResumeLayout(false);
            this.grb_targets.PerformLayout();
            this.grb_Optimize.ResumeLayout(false);
            this.grb_Optimize.PerformLayout();
            this.grb_Ongoing.ResumeLayout(false);
            this.grb_Ongoing.PerformLayout();
            this.grb_TargetQuantity.ResumeLayout(false);
            this.grb_TargetQuantity.PerformLayout();
            this.grb_powerSave.ResumeLayout(false);
            this.grb_powerSave.PerformLayout();
            this.grb_Repeat.ResumeLayout(false);
            this.grb_Repeat.PerformLayout();
            this.grb_multi_ant.ResumeLayout(false);
            this.grb_multi_ant.PerformLayout();
            this.grb_ants_g1.ResumeLayout(false);
            this.grb_ants_g1.PerformLayout();
            this.grb_temp_pow_ants_g1.ResumeLayout(false);
            this.grb_temp_pow_ants_g1.PerformLayout();
            this.grb_ants_g2.ResumeLayout(false);
            this.grb_ants_g2.PerformLayout();
            this.grb_temp_pow_ants_g2.ResumeLayout(false);
            this.grb_temp_pow_ants_g2.PerformLayout();
            this.grb_real_inv_ants.ResumeLayout(false);
            this.grb_real_inv_ants.PerformLayout();
            this.flowLayoutPanel5.ResumeLayout(false);
            this.groupBox9.ResumeLayout(false);
            this.groupBox9.PerformLayout();
            this.groupBox12.ResumeLayout(false);
            this.groupBox12.PerformLayout();
            this.groupBox22.ResumeLayout(false);
            this.panel14.ResumeLayout(false);
            ((System.ComponentModel.ISupportInitialize)(this.dgvTagMask)).EndInit();
            this.groupBox26.ResumeLayout(false);
            this.groupBox26.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.dgvInventoryTagResults)).EndInit();
            this.groupBox25.ResumeLayout(false);
            this.groupBox25.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.led_total_tagreads)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.led_totalread_count)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.led_cmd_readrate)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.led_cmd_execute_duration)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.ledFast_total_execute_time)).EndInit();
            this.groupBox2.ResumeLayout(false);
            this.grb_inventory_type.ResumeLayout(false);
            this.grb_inventory_type.PerformLayout();
            this.groupBox27.ResumeLayout(false);
            this.groupBox27.PerformLayout();
            this.pageAcessTag.ResumeLayout(false);
            this.gbCmdOperateTag.ResumeLayout(false);
            this.gbCmdOperateTag.PerformLayout();
            this.groupBox14.ResumeLayout(false);
            this.grbSensorType.ResumeLayout(false);
            this.grbSensorType.PerformLayout();
            this.groupBox28.ResumeLayout(false);
            this.groupBox28.PerformLayout();
            this.grbReadTagMultiBank.ResumeLayout(false);
            this.grbReadTagMultiBank.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.dgvTagOp)).EndInit();
            this.groupBox3.ResumeLayout(false);
            this.groupBox3.PerformLayout();
            this.groupBox31.ResumeLayout(false);
            this.groupBox31.PerformLayout();
            this.groupBox16.ResumeLayout(false);
            this.groupBox16.PerformLayout();
            this.groupBox15.ResumeLayout(false);
            this.groupBox19.ResumeLayout(false);
            this.groupBox19.PerformLayout();
            this.groupBox18.ResumeLayout(false);
            this.groupBox18.PerformLayout();
            this.groupBox13.ResumeLayout(false);
            this.groupBox13.PerformLayout();
            this.PagTranDataLog.ResumeLayout(false);
            this.panel3.ResumeLayout(false);
            this.panel3.PerformLayout();
            this.net_configure_tabPage.ResumeLayout(false);
            this.net_configure_tabPage.PerformLayout();
            this.groupBox20.ResumeLayout(false);
            this.groupBox17.ResumeLayout(false);
            this.groupBox17.PerformLayout();
            this.port_setting_tabcontrol.ResumeLayout(false);
            this.net_port_0_tabPage.ResumeLayout(false);
            this.net_port_0_tabPage.PerformLayout();
            this.grbDnsDomain.ResumeLayout(false);
            this.grbDnsDomain.PerformLayout();
            this.grbDesIpPort.ResumeLayout(false);
            this.grbDesIpPort.PerformLayout();
            this.net_port_1_tabPage.ResumeLayout(false);
            this.net_port_1_tabPage.PerformLayout();
            this.grbHeartbeat.ResumeLayout(false);
            this.grbHeartbeat.PerformLayout();
            this.net_base_settings_gb.ResumeLayout(false);
            this.net_base_settings_gb.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.dgvNetPort)).EndInit();
            this.groupBox30.ResumeLayout(false);
            this.groupBox30.PerformLayout();
            this.PagSpecialFeature.ResumeLayout(false);
            this.groupBox39.ResumeLayout(false);
            this.groupBox39.PerformLayout();
            this.groupBox40.ResumeLayout(false);
            this.groupBox40.PerformLayout();
            this.tableLayoutPanel3.ResumeLayout(false);
            this.panel6.ResumeLayout(false);
            this.panel7.ResumeLayout(false);
            this.panel7.PerformLayout();
            this.groupBox8.ResumeLayout(false);
            this.groupBox8.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.ledControl9)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.ledControl10)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.ledControl11)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.ledControl12)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.ledControl13)).EndInit();
            this.panel1.ResumeLayout(false);
            this.panel1.PerformLayout();
            ((System.ComponentModel.ISupportInitialize)(this.ledControl14)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.ledControl15)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.ledControl16)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.ledControl17)).EndInit();
            ((System.ComponentModel.ISupportInitialize)(this.ledControl18)).EndInit();
            this.ResumeLayout(false);

        }
        #endregion

        private TabControl tabCtrMain;
        private TabPage PagReaderSetting;
        private LogRichTextBox lrtxtLog;
        private TabPage PagTranDataLog;
        private Label label35;
        private Button btnSendData;
        private Label label17;
        private HexTextBox htxtSendData;
        private Label label16;
        private LogRichTextBox lrtxtDataTran;
        private HexTextBox htxtCheckData;
        private Button btnClearData;
        private CheckBox ckDisplayLog;
        private TabPage pageEpcTest;
        private TableLayoutPanel tableLayoutPanel3;
        private Panel panel6;
        private Button button4;
        private Panel panel7;
        private CheckBox checkBox5;
        private CheckBox checkBox6;
        private CheckBox checkBox7;
        private CheckBox checkBox8;
        private TextBox textBox5;
        private TextBox textBox6;
        private Button button5;
        private Label label76;
        private Label label77;
        private Label label78;
        private GroupBox groupBox8;
        private ComboBox comboBox9;
        private Led ledControl9;
        private Led ledControl10;
        private Led ledControl11;
        private Led ledControl12;
        private Label label79;
        private Label label80;
        private Label label81;
        private Label label82;
        private Label label83;
        private Led ledControl13;
        private ListView listView1;
        private ColumnHeader columnHeader43;
        private ColumnHeader columnHeader44;
        private ColumnHeader columnHeader45;
        private ColumnHeader columnHeader46;
        private ColumnHeader columnHeader47;
        private ColumnHeader columnHeader48;
        private ComboBox comboBox10;
        private Led ledControl14;
        private Led ledControl15;
        private Led ledControl16;
        private Led ledControl17;
        private Label label87;
        private Label label88;
        private Label label89;
        private Label label90;
        private Label label91;
        private Led ledControl18;
        private TabControl tabControl_baseSettings;
        private TabPage tabPage1;
        private GroupBox gbCmdReadGpio;
        private Button btnWriteGpio4Value;
        private Button btnWriteGpio3Value;
        private GroupBox groupBox7;
        private Label label32;
        private RadioButton rdbGpio4High;
        private RadioButton rdbGpio4Low;
        private GroupBox groupBox6;
        private Label label33;
        private RadioButton rdbGpio3High;
        private RadioButton rdbGpio3Low;
        private GroupBox groupBox5;
        private Label label31;
        private RadioButton rdbGpio2High;
        private RadioButton rdbGpio2Low;
        private GroupBox groupBox4;
        private Label label30;
        private RadioButton rdbGpio1High;
        private RadioButton rdbGpio1Low;
        private Button btnReadGpioValue;
        private GroupBox gbCmdBeeper;
        private Button btnSetBeeperMode;
        private GroupBox gbCmdTemperature;
        private Button btnGetReaderTemperature;
        private TextBox txtReaderTemperature;
        private GroupBox gbCmdVersion;
        private Button btnGetFirmwareVersion;
        private TextBox txtFirmwareVersion;
        private Button btnResetReader;
        private GroupBox gbCmdBaudrate;
        private HexTextBox htbGetIdentifier;
        private HexTextBox htbSetIdentifier;
        private Button btSetIdentifier;
        private Button btGetIdentifier;
        private GroupBox gbCmdReaderAddress;
        private HexTextBox htxtReadId;
        private Button btnSetReadAddress;
        private GroupBox grb_tcp;
        private TextBox txtTcpPort;
        private IpAddressTextBox ipIpServer;
        private Label label4;
        private Label label3;
        private GroupBox grb_rs232;
        private Button btnSetUartBaudrate;
        private ComboBox cmbSetBaudrate;
        private Button btnConnect;
        private ComboBox cmbBaudrate;
        private ComboBox cmbComPort;
        private Label label2;
        private Label label1;
        private GroupBox gbConnectType;
        private RadioButton radio_btn_tcp;
        private RadioButton radio_btn_rs232;
        private TabPage tabPage2;
        private GroupBox gbMonza;
        private RadioButton rdbMonzaOff;
        private Button btSetMonzaStatus;
        private Button btGetMonzaStatus;
        private RadioButton rdbMonzaOn;
        private GroupBox gbCmdAntenna;
        private Button btnGetWorkAntenna;
        private Button btnSetWorkAntenna;
        private GroupBox gbCmdAntDetector;
        private Button btnGetAntDetector;
        private Button btnSetAntDetector;
        private GroupBox gbCmdRegion;
        private Button btnGetFrequencyRegion;
        private Button btnSetFrequencyRegion;
        private GroupBox gbCmdOutputPower;
        private Button btnGetOutputPower;
        private Button btnSetOutputPower;
        private Label label9;
        private Button btReaderSetupRefresh;
        private Button btRfSetup;
        private GroupBox groupBox10;
        private GroupBox groupBox11;
        private TextBox tbAntDectector;
        private Label label8;
        private Label label10;
        private Label label5;
        private Label label6;
        private Label label7;
        private Label label14;
        private Label label11;
        private GroupBox gbProfile;
        private GroupBox groupBox23;
        private TextBox textFreqQuantity;
        private TextBox TextFreqInterval;
        private TextBox textStartFreq;
        private GroupBox groupBox21;
        private Label label37;
        private Label label36;
        private ComboBox cmbFrequencyEnd;
        private Label label13;
        private ComboBox cmbFrequencyStart;
        private Label label12;
        private RadioButton rdbRegionChn;
        private RadioButton rdbRegionEtsi;
        private RadioButton rdbRegionFcc;
        private Label label106;
        private Label label105;
        private Label label104;
        private Label label103;
        private Label label86;
        private Label label75;
        private GroupBox gbReturnLoss;
        private Label label108;
        private TextBox textReturnLoss;
        private Button btReturnLoss;
        private Label label107;
        private ComboBox cmbWorkAnt;
        private Label label110;
        private Label label109;
        private ComboBox cmbReturnLossFreq;
        private CheckBox ckClearOperationRec;
        private CheckBox cbUserDefineFreq;
        private Label label34;
        private Label label21;
        private Label label20;
        private Label label18;
        private TextBox tb_outputpower_4;
        private TextBox tb_outputpower_3;
        private TextBox tb_outputpower_2;
        private TextBox tb_outputpower_1;
        private Label label15;
        private Label label115;
        private Label label114;
        private Label label113;
        private Label label112;
        private TextBox tb_outputpower_8;
        private TextBox tb_outputpower_7;
        private TextBox tb_outputpower_6;
        private TextBox tb_outputpower_5;
        private GroupBox groupBox24;
        private RadioButton antType8;
        private RadioButton antType4;
        private RadioButton antType1;
        private Button btnSaveData;
        private RadioButton antType16;
        private Label label151;
        private Label label152;
        private Label label153;
        private Label label154;
        private TextBox tb_outputpower_16;
        private TextBox tb_outputpower_15;
        private TextBox tb_outputpower_14;
        private TextBox tb_outputpower_13;
        private Label label147;
        private Label label148;
        private Label label149;
        private Label label150;
        private TextBox tb_outputpower_12;
        private TextBox tb_outputpower_11;
        private TextBox tb_outputpower_10;
        private TextBox tb_outputpower_9;
        private TabPage net_configure_tabPage;
        private LinkLabel linklblNetPortCfgTool_Link;
        private Label label165;
        private Label label164;
        private LinkLabel linklblOldNetPortCfgTool_Link;
        private Button btnClearNetPort;
        private GroupBox net_base_settings_gb;
        private TextBox txtbxHwCfgMac;
        private Label label157;
        private CheckBox chkbxHwCfgDhcpEn;
        private TextBox txtbxHwCfgGateway;
        private TextBox txtbxHwCfgMask;
        private TextBox txtbxHwCfgIp;
        private TextBox txtbxHwCfgDeviceName;
        private Label label161;
        private Label label160;
        private Label label158;
        private Label label156;
        private DataGridView dgvNetPort;
        private Label label159;
        private ComboBox cmbbxNetCard;
        private GroupBox groupBox30;
        private Label lblCurPcMac;
        private Label lblCurNetcard;
        private Button btnResetNetport;
        private Button btnSetNetport;
        private Button btnGetNetport;
        private Button btnSearchNetport;
        private Button net_refresh_netcard_btn;
        private TabControl port_setting_tabcontrol;
        private TabPage net_port_0_tabPage;
        private CheckBox chkbxPort1_RandEn;
        private Label label169;
        private ComboBox cmbbxPort1_Parity;
        private Label label168;
        private ComboBox cmbbxPort1_StopBits;
        private Label label167;
        private ComboBox cmbbxPort1_DataSize;
        private Label label166;
        private ComboBox cmbbxPort1_BaudRate;
        private TextBox txtbxPort1_DesPort;
        private TextBox txtbxPort1_DesIp;
        private TextBox txtbxPort1_NetPort;
        private Label label126;
        private Label label125;
        private ComboBox cmbbxPort1_NetMode;
        private TabPage net_port_1_tabPage;
        private TextBox txtbxHeartbeatInterval;
        private Label label174;
        private Label label175;
        private TextBox txtbxHeartbeatContent;
        private CheckBox chkbxPort1_PortEn;
        private Button btnDefaultNetPort;
        private CheckBox chkbxPort1_PhyDisconnect;
        private Label label180;
        private Label label192;
        private Label label190;
        private Label label191;
        private CheckBox chkbxPort1_ResetCtrl;
        private Label label189;
        private TextBox txtbxPort1_RxTimeout;
        private Label label188;
        private TextBox txtbxPort1_RxPkgLen;
        private TextBox txtbxPort1_DnsDomain;
        private Label label193;
        private CheckBox chkbxHwCfgComCfgEn;
        private CheckBox chkbxPort1_DomainEn;
        private Label label128;
        private TextBox txtbxPort1_ReConnectCnt;
        private Label label203;
        private TextBox txtbxPort1_Dnsport;
        private Label label202;
        private TextBox txtbxPort1_DnsIp;
        private CheckBox chkbxPort0PortEn;
        private Label lblNetPortCount;
        private Button net_load_cfg_btn;
        private Button net_save_cfg_btn;
        private Button btn_refresh_comports;
        private TabControl tab_6c_Tags_Test;
        private TabPage pageFast4AntMode;
        private TabPage pageAcessTag;
        private GroupBox gbCmdOperateTag;
        private GroupBox groupBox16;
        private Button btnKillTag;
        private HexTextBox htxtKillPwd;
        private Label label29;
        private GroupBox groupBox15;
        private GroupBox groupBox19;
        private RadioButton rdbUserMemory;
        private RadioButton rdbTidMemory;
        private RadioButton rdbEpcMermory;
        private RadioButton rdbKillPwd;
        private RadioButton rdbAccessPwd;
        private GroupBox groupBox18;
        private RadioButton rdbLockEver;
        private RadioButton rdbFreeEver;
        private RadioButton rdbLock;
        private RadioButton rdbFree;
        private Button btnLockTag;
        private RadioButton radio_btnBlockWrite;
        private RadioButton radio_btnWrite;
        private HexTextBox hexTb_WriteData;
        private TextBox tb_wordLen;
        private Label label27;
        private Button btnWriteTag;
        private Button btnReadTag;
        private TextBox tb_startWord;
        private Label label26;
        private RadioButton rdbUser;
        private RadioButton rdbTid;
        private RadioButton rdbEpc;
        private RadioButton rdbReserved;
        private Label label24;
        private GroupBox groupBox13;
        private Label label23;
        private Button btnSetAccessEpcMatch;
        private ComboBox cmbSetAccessEpcMatch;
        private TextBox txtAccessEpcMatch;
        private GroupBox groupBox26;
        private Label txtCmdTagCount;
        private Label label49;
        private Label label22;
        private DataGridView dgvInventoryTagResults;
        private DataGridViewTextBoxColumn SerialNumber_fast_inv;
        private DataGridViewTextBoxColumn ReadCount_fast_inv;
        private DataGridViewTextBoxColumn PC_fast_inv;
        private DataGridViewTextBoxColumn EPC_fast_inv;
        private DataGridViewTextBoxColumn Antenna_fast_inv;
        private DataGridViewTextBoxColumn Freq_fast_inv;
        private DataGridViewTextBoxColumn Rssi_fast_inv;
        private DataGridViewTextBoxColumn Phase_fast_inv;
        private DataGridViewTextBoxColumn Data_fast_inv;
        private Button btnFastRefresh;
        private TextBox txtFastMinRssi;
        private Button btnSaveTags;
        private TextBox txtFastMaxRssi;
        private GroupBox groupBox25;
        private Led led_total_tagreads;
        private Label label58;
        private Led led_totalread_count;
        private Led led_cmd_readrate;
        private Label label55;
        private Label label56;
        private Led led_cmd_execute_duration;
        private Label label57;
        private Label label54;
        private Led ledFast_total_execute_time;
        private GroupBox groupBox2;
        private Button btnInventory;
        private TextBox tb_fast_inv_staytargetB_times;
        private CheckBox cb_fast_inv_reverse_target;
        private FlowLayoutPanel flowLayoutPanel1;
        private CheckBox cb_fast_inv_check_all_ant;
        private CheckBox chckbx_fast_inv_ant_8;
        private CheckBox chckbx_fast_inv_ant_7;
        private CheckBox chckbx_fast_inv_ant_6;
        private CheckBox chckbx_fast_inv_ant_5;
        private CheckBox chckbx_fast_inv_ant_4;
        private CheckBox chckbx_fast_inv_ant_3;
        private TextBox txt_fast_inv_Stay_8;
        private TextBox txt_fast_inv_Stay_7;
        private TextBox txt_fast_inv_Stay_6;
        private TextBox txt_fast_inv_Stay_5;
        private TextBox txt_fast_inv_Stay_4;
        private TextBox txt_fast_inv_Stay_3;
        private TextBox txt_fast_inv_Stay_2;
        private TextBox txt_fast_inv_Stay_1;
        private CheckBox chckbx_fast_inv_ant_1;
        private CheckBox chckbx_fast_inv_ant_2;
        private CheckBox chckbx_fast_inv_ant_9;
        private CheckBox chckbx_fast_inv_ant_10;
        private CheckBox chckbx_fast_inv_ant_11;
        private CheckBox chckbx_fast_inv_ant_12;
        private CheckBox chckbx_fast_inv_ant_13;
        private CheckBox chckbx_fast_inv_ant_14;
        private CheckBox chckbx_fast_inv_ant_15;
        private CheckBox chckbx_fast_inv_ant_16;
        private TextBox txt_fast_inv_Stay_9;
        private TextBox txt_fast_inv_Stay_10;
        private TextBox txt_fast_inv_Stay_11;
        private TextBox txt_fast_inv_Stay_12;
        private TextBox txt_fast_inv_Stay_13;
        private TextBox txt_fast_inv_Stay_14;
        private TextBox txt_fast_inv_Stay_15;
        private TextBox txt_fast_inv_Stay_16;
        private GroupBox groupBox27;
        private TextBox txtTargetQuantity;
        private TextBox txtOngoing;
        private TextBox txtOptimize;
        private CheckBox cb_use_Phase;
        private CheckBox cb_customized_session_target;
        private TextBox txtInterval;
        private TextBox txtRepeat;
        private TextBox tb_fast_inv_reserved_1;
        private TextBox tb_fast_inv_reserved_2;
        private TextBox tb_fast_inv_reserved_5;
        private TextBox tb_fast_inv_reserved_4;
        private TextBox tb_fast_inv_reserved_3;
        private Label lblInvExecTime;
        private TextBox mInventoryExeCount;
        private Label lblInvCmdInterval;
        private TextBox mFastIntervalTime;
        private GroupBox grb_sessions;
        private RadioButton radio_btn_S0;
        private RadioButton radio_btn_S1;
        private RadioButton radio_btn_S2;
        private RadioButton radio_btn_S3;
        private GroupBox grb_targets;
        private RadioButton radio_btn_target_A;
        private RadioButton radio_btn_target_B;
        private TextBox tv_temp_pow_16;
        private TextBox tv_temp_pow_15;
        private TextBox tv_temp_pow_14;
        private TextBox tv_temp_pow_13;
        private TextBox tv_temp_pow_12;
        private TextBox tv_temp_pow_11;
        private TextBox tv_temp_pow_10;
        private TextBox tv_temp_pow_9;
        private TextBox tv_temp_pow_4;
        private TextBox tv_temp_pow_3;
        private TextBox tv_temp_pow_2;
        private TextBox tv_temp_pow_1;
        private GroupBox grb_selectFlags;
        private RadioButton radio_btn_sl_03;
        private RadioButton radio_btn_sl_02;
        private RadioButton radio_btn_sl_01;
        private RadioButton radio_btn_sl_00;
        private GroupBox grb_inventory_type;
        private RadioButton radio_btn_fast_inv;
        private RadioButton radio_btn_realtime_inv;
        private ComboBox combo_realtime_inv_ants;
        private GroupBox grb_real_inv_ants;
        private Label label61;
        private GroupBox grb_ants_g2;
        private GroupBox grb_multi_ant;
        private GroupBox grb_ants_g1;
        private GroupBox grb_temp_pow_ants_g1;
        private GroupBox grb_temp_pow_ants_g2;
        private TextBox tv_temp_pow_6;
        private TextBox tv_temp_pow_5;
        private TextBox tv_temp_pow_7;
        private TextBox tv_temp_pow_8;
        private GroupBox grb_Interval;
        private GroupBox grb_Repeat;
        private GroupBox grb_Optimize;
        private GroupBox grb_Ongoing;
        private GroupBox grb_TargetQuantity;
        private GroupBox grb_Reserve;
        private GroupBox grb_powerSave;
        private TextBox txtPowerSave;
        private GroupBox grb_inventory_cfg;
        private CheckBox cb_use_powerSave;
        private CheckBox cb_use_selectFlags_tempPows;
        private CheckBox cb_use_optimize;
        private Label label53;
        private FlowLayoutPanel flowLayoutPanel2;
        private GroupBox groupBox1;
        private HexTextBox hexTb_accessPw;
        private Panel panel1;
        private Panel panel3;
        private DataGridView dgvTagOp;
        private CheckBox cb_tagFocus;
        private GroupBox grbHeartbeat;
        private GroupBox grbDesIpPort;
        private GroupBox grbDnsDomain;
        private Button btnCancelAccessEpcMatch;
        private Button btnGetAccessEpcMatch;
        private GroupBox groupBox3;
        private GroupBox grbReadTagMultiBank;
        private Label label68;
        private Label label67;
        private Label label66;
        private TextBox txtbxReadTagUserCnt;
        private Label label64;
        private TextBox txtbxReadTagUserAddr;
        private Label label65;
        private TextBox txtbxReadTagTidCnt;
        private Label label59;
        private TextBox txtbxReadTagTidAddr;
        private Label label63;
        private TextBox txtbxReadTagResCnt;
        private Label label28;
        private TextBox txtbxReadTagResAddr;
        private Label label25;
        private ComboBox cmbbxReadTagReadMode;
        private ComboBox cmbbxReadTagTarget;
        private ComboBox cmbbxReadTagSession;
        private GroupBox groupBox28;
        private GroupBox groupBox31;
        private Button btnClearTagOpResult;
        private CheckBox chkbxReadSensorTag;
        private GroupBox grbSensorType;
        private RadioButton radio_btn_johar_1;
        private Button btnStartReadSensorTag;
        private CheckBox chkbxReadTagMultiBankEn;
        private GroupBox groupBox14;
        private ComboBox cmbbxTagOpWorkAnt;
        private Button btnSetTagOpWorkAnt;
        private Button btnGetTagOpWorkAnt;
        private CheckBox chkbxReadBuffer;
        private CheckBox chkbxSaveLog;
        private GroupBox grbModuleBaudRate;
        private Label label69;
        private GroupBox groupBox17;
        private GroupBox groupBox20;
        private Button btGetProfile;
        private Button btSetProfile;
        private FlowLayoutPanel flowLayoutPanel3;
        private DataGridViewTextBoxColumn tagOp_SerialNumberColumn;
        private DataGridViewTextBoxColumn tagOp_PcColumn;
        private DataGridViewTextBoxColumn tagOp_CrcColumn;
        private DataGridViewTextBoxColumn tagOp_EpcColumn;
        private DataGridViewTextBoxColumn tagOp_DataColumn;
        private DataGridViewTextBoxColumn tagOp_DataLenColumn;
        private DataGridViewTextBoxColumn tagOp_AntennaColumn;
        private DataGridViewTextBoxColumn tagOp_OpCountColumn;
        private DataGridViewTextBoxColumn tagOp_FreqColumn;
        private DataGridViewTextBoxColumn tagOp_TemperatureColumn;
        private ComboBox cmbModuleLink;
        private GroupBox gbModel;
        private RadioButton rb_R2000;
        private RadioButton rb_E710;
        private TabPage tabPage4;
        private FlowLayoutPanel flowLayoutPanel4;
        private GroupBox gbRfLink;
        private CheckBox cbDrmSwich;
        private Label label19;
        private Label label40;
        private ComboBox cbbE710RfLink;
        private Button btGetE710Profile;
        private Button btSetE710Profile;
        private GroupBox grpbQ;
        private GroupBox groupBox33;
        private RadioButton rbStQ;
        private RadioButton rbDyQ;
        private GroupBox groupBox34;
        private Label label43;
        private ComboBox cbbMinQValue;
        private Label label42;
        private ComboBox cbbInitQValue;
        private Label label41;
        private ComboBox cbbMaxQValue;
        private Button btSetQValue;
        private Button btGetQValue;
        private Label label45;
        private Label label44;
        private TextBox tbMaxQSince;
        private TextBox tbNumMinQ;
        private Button btE710Refresh;
        private RadioButton rb_fast_inv;
        private CheckBox cb_IceBoxTest;
        private Label label47;
        private TextBox tb_InvCntTime;
        private CheckBox cb_InvTime;
        private TabPage tabPage5;
        private GroupBox groupBox29;
        private Button btSetTm600Profile;
        private Button btGetTm600Profile;
        private ComboBox cbbTm600RFLink;
        private Label label46;
        private GroupBox groupBox32;
        private GroupBox groupBox35;
        private Label label50;
        private ComboBox cbbTestModel;
        private Label label48;
        private TextBox tbTestCnt;
        private TextBox tbCmdLen;
        private Label label51;
        private Button btnSerialTest;
        private TextBox tbTestCmd;
        private Label label52;
        private GroupBox groupBox36;
        private GroupBox groupBox38;
        private GroupBox groupBox37;
        private Label label60;
        private Label label70;
        private Label lbPCSendCnt;
        private Label lbModelSendCnt;
        private Label label85;
        private Label label74;
        private Label lbModelRevCnt;
        private Label lbPCRecCnt;
        private Label label92;
        private Label label95;
        private Label lbModelTestTimeCnt;
        private Label label97;
        private Label label94;
        private Label lbPCTestTimeCnt;
        private CheckBox cbSendPeroid;
        private Label label62;
        private TextBox tbSendPeroid;
        private Label label72;
        private FlowLayoutPanel flowLayoutPanel5;
        private GroupBox groupBox9;
        private ComboBox cmbbxSessionId;
        private TextBox bitLen;
        private TextBox startAddr;
        private HexTextBox hexTextBox_mask;
        private Label label38;
        private ComboBox combo_mast_id;
        private Label label39;
        private Label label71;
        private Label label99;
        private Label label100;
        private Label label101;
        private Label label102;
        private ComboBox combo_menbank;
        private ComboBox combo_action;
        private Button btnTagSelect;
        private GroupBox groupBox12;
        private Label label111;
        private ComboBox combo_mast_id_Clear;
        private Button btnClearTagMask;
        private GroupBox groupBox22;
        private Button btnGetTagMask;
        private Panel panel14;
        private DataGridView dgvTagMask;
        private DataGridViewTextBoxColumn tagMask_MaskNoColumn;
        private DataGridViewTextBoxColumn tagMask_SessionIdColumn;
        private DataGridViewTextBoxColumn tagMask_ActionColumn;
        private DataGridViewTextBoxColumn tagMask_MembankColumn;
        private DataGridViewTextBoxColumn tagMask_StartAddrColumn;
        private DataGridViewTextBoxColumn tagMask_MaskLenColumn;
        private DataGridViewTextBoxColumn tagMask_MaskValueColumn;
        private DataGridViewTextBoxColumn tagMask_TruncateColumn;
        private Panel panel2;
        private LinkLabel lLbConfig;
        private LinkLabel lLbTagFilter;
        private TabPage PagSpecialFeature;
        private ComboBox cbbBeepStatus;
        private Button btnFactoryReset;
        private GroupBox groupBox39;
        private Label label73;
        private GroupBox groupBox40;
        private TextBox tb_Interval;
        private Label label84;
        private Button btn_GetAntSwitch;
        private Button btn_SetAntSwitch;
        private Label label93;
        private Label label96;
        private TextBox txtDStay;
        private ComboBox cmbAntSelect4;
        private Label label98;
        private Label label116;
        private TextBox txtCStay;
        private ComboBox cmbAntSelect3;
        private Label label117;
        private Label label118;
        private TextBox txtBStay;
        private ComboBox cmbAntSelect2;
        private Label label119;
        private Label label120;
        private TextBox txtAStay;
        private ComboBox cmbAntSelect1;
        private ComboBox cbb_FunctionId;
        private Button btn_SetFunction;
        private Button btn_GetFunction;
        private Label label121;
        private Label label122;
        private TextBox txtHStay;
        private ComboBox cmbAntSelect8;
        private Label label123;
        private Label label124;
        private TextBox txtGStay;
        private ComboBox cmbAntSelect7;
        private Label label127;
        private Label label129;
        private TextBox txtFStay;
        private ComboBox cmbAntSelect6;
        private Label label130;
        private Label label131;
        private TextBox txtEStay;
        private ComboBox cmbAntSelect5;
        private LinkLabel linkLabel1;
        private CheckBox cbMulAnt;
        private Button btn_RefreshSpecial;
        private DataGridViewCheckBoxColumn npSerialNumberColumn;
        private DataGridViewTextBoxColumn npDeviceNameColumn;
        private DataGridViewTextBoxColumn npDeviceIpColumn;
        private DataGridViewTextBoxColumn npDeviceMacColumn;
        private DataGridViewTextBoxColumn npChipVerColumn;
        private DataGridViewTextBoxColumn npPcMacColumn;
    }
}