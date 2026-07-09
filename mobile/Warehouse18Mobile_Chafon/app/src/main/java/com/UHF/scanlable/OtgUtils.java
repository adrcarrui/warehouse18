package com.UHF.scanlable;

import android.device.DeviceManager;
import android.text.TextUtils;
import android.util.Log;

import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class OtgUtils {

    private static final String TAG = OtgUtils.class.getSimpleName();
    private static DeviceManager mDeviceManager = new DeviceManager();
    private static List<String> listEnable = new ArrayList<>();
    private static List<String> listDisable = new ArrayList<>();

    private static int NUM_ENABLE_SIZE = 5;
    private static int NUM_DISABLE_SIZE = 4;

    static {

        //TODO 已上电的标识
        listEnable.add("enable");
        listEnable.add("active");
        listEnable.add("1");
        listEnable.add("2");
        listEnable.add("3");
        //TODO 已下电的标识
        listDisable.add("disable");
        listDisable.add("suspend");
        listDisable.add("0");
        listDisable.add("6");
    }

    private static final String PROJECT_SQ53 = "SQ53";
    private static final String PROJECT_SQ53C = "SQ53C";
    private static final String PROJECT_SQ53Q = "SQ53Q";
    private static final String PROJECT_SQ53B = "SQ53B";
    private static final String PROJECT_SQ53Z = "SQ53Z";
    private static final String PROJECT_SQ53X = "SQ53X";
    private static final String PROJECT_SQ53S = "SQ53S";
    private static final String PROJECT_SQ55 = "SQ55";
    private static final String PROJECT_SQ55_5G = "SQ55_5G";
    private static final String PROJECT_SQ55_5G_1 = "SQ55-5G";
    private static final String PROJECT_SQ81 = "SQ81";

    private static final String NODE_POGO_UART = "/sys/devices/soc/c170000.serial/pogo_uart";
    private static final String NODE_USB_SWITCH = "/sys/devices/virtual/Usb_switch/usbswitch/function_otg_en";
    private static final String NODE_POGO_5V = "/sys/devices/soc/soc:sectrl/ugp_ctrl/gp_pogo_5v_ctrl/enable";
    private static final String NODE_OTG_EN_CTRL = "/sys/devices/soc/soc:sectrl/ugp_ctrl/gp_otg_en_ctrl/enable";
    private static final String NOde_53X = "/sys/kernel/kobject_pogo_otg_status/pogo_otg_status";
    private static final String NOde_53S = "/sys/devices/virtual/pogo/pogo_pin/pogo_otg_vbus";
    private static final String NODE_53B = "/sys/devices/platform/otg_typecdig/pogo_5v";

    //    private static final String NODE_53B =   "/sys/kernel/kobject_pogo_otg_status/pogo_otg5v_en";
    private static final String NODE_55_5G = "/sys/devices/platform/otg_iddig/pogo_5v";
    private static final String NODE_81 = "/sys/devices/platform/soc/soc:meig-gpios/meig-gpios/otg_enable";

    public static boolean setPOGOPINEnable(final boolean enable) {

        try {

            String mProjectName = mDeviceManager.getSettingProperty("pwv.project");
            String node5v = mDeviceManager.getSettingProperty("persist.sys.pogopin.otg5v.en");

            Log.v(TAG, "projectName:" + mProjectName + "    enable:" + enable + "    node5v:" + node5v);

//        if (!TextUtils.isEmpty(mProjectName)){
//            return true;
//        }

            if (TextUtils.equals(mProjectName, PROJECT_SQ53Q)) { //53Q 上电
                if (isChange(NODE_POGO_UART, enable)) {
                    powerControl0X31(NODE_POGO_UART, enable);
                }
                if (isChange(NODE_POGO_5V, enable)) {
                    powerControl0X31(NODE_POGO_5V, enable);
                }
            } else if (TextUtils.equals(mProjectName, PROJECT_SQ53C)) {
                if (isChange(NODE_POGO_5V, enable)) {
                    powerControl0X31(NODE_POGO_5V, enable);
                }
                if (isChange(NODE_OTG_EN_CTRL, enable)) {
                    powerControl0X31(NODE_OTG_EN_CTRL, enable);
                }
            }else if (TextUtils.equals(mProjectName, PROJECT_SQ53S)) {
//                if (!TextUtils.isEmpty(NOde_53S) && isChange(node5v, enable)) {
                if (!TextUtils.isEmpty(node5v) && isChange(node5v, enable)) {
                    powerControl0X31(node5v, enable);
                }
            }  else if (TextUtils.equals(mProjectName, PROJECT_SQ81)) {
                if (isChange(NODE_81, enable)) {
                    powerControl0X33(NODE_81, enable);
                }
            } else if (TextUtils.equals(mProjectName, PROJECT_SQ53) || TextUtils.equals(mProjectName, PROJECT_SQ53Z)) { //53 、53Z上电
                if (isChange(NODE_POGO_UART, enable)) {
                    powerControl0X31(NODE_POGO_UART, enable);
                }
                if (isChange(NODE_USB_SWITCH, enable)) {
                    powerControl0X32(NODE_USB_SWITCH, enable);
                }
            } else if (TextUtils.equals(mProjectName, PROJECT_SQ53B)  ) {

                if (isChange(NODE_53B, enable)) {
                    powerControl0X31(NODE_53B, enable);
                }
            } else if (  TextUtils.equals(mProjectName, PROJECT_SQ55_5G)||TextUtils.equals(mProjectName, PROJECT_SQ55_5G_1)) {

                if (isChange(NODE_55_5G, enable)) {
                    powerControl0X31(NODE_55_5G, enable);
                }
            }  else if (!TextUtils.isEmpty(node5v)) {

                if (isChange(node5v, enable)) {
                    powerControl0X31(node5v, enable);
                }

                if (TextUtils.equals(mProjectName, PROJECT_SQ53X) || TextUtils.equals(mProjectName, PROJECT_SQ53B) ) {
                    if (TextUtils.equals(mProjectName, PROJECT_SQ53X)) {

                        if (isChange(NOde_53X, enable)) {
                            if (isOtgOsVersion53X()) {
                                Log.v(TAG, "53X    -->   ");
                                powerControl0X31(NOde_53X, enable);
                            }
                        }
                    }else {
                        if(isChange(NOde_53X, enable)) {
                            powerControl0X31(NOde_53X, enable);
                        }
                    }
                }
            } else { //other
                Log.v(TAG, "device model not found  : " + mProjectName);
                return true;
            }

            return true;
        } catch (Throwable e) {
            e.printStackTrace();
            Log.v(TAG, "Exception:" + e.getMessage());
            return false;
        }
    }

    private static boolean isOtgOsVersion53X(){
        //获取OS硬件版本
        try {
            String   osVersion =new DeviceManager().getSettingProperty("ro.vendor.build.id");
            String timeStr = osVersion.substring(26,32);
            Log.v(TAG,"isOtgOsVersion53X()   "+osVersion+"    -->   "+timeStr);
            int time = Integer.parseInt(timeStr);
            if (time>=230220){//53X 新OS不需上电这个节点
                return false;
            }else {
                return true;
            }
        } catch (Throwable e) {
            e.printStackTrace();
            return true;
        }

    }
    private static void powerControl0X31(String node5v, boolean enable) throws Throwable {
        FileOutputStream node_1 = null;
        try {
            byte[] open_one = new byte[]{0x31};
            byte[] close = new byte[]{0x30};
            node_1 = new FileOutputStream(node5v);
            node_1.write(enable ? open_one : close);
            Log.v("OtgUtils", "write  success :" + node5v);
        } catch (Throwable e) {
            e.printStackTrace();
        } finally {
            try {
                if (node_1 != null) {
                    node_1.close();
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    private static void powerControl0X32(String node5v, boolean enable) throws Throwable {
        FileOutputStream node_2 = null;
        try {
            byte[] open_two = new byte[]{0x32};
            byte[] close = new byte[]{0x30};
            node_2 = new FileOutputStream(node5v);
            node_2.write(enable ? open_two : close);
            Log.v("OtgUtils", "write  success :" + node5v);
        } catch (Throwable e) {
            e.printStackTrace();
        } finally {
            try {
                if (node_2 != null) {
                    node_2.close();
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }

    }

    private static void powerControl0X33(String node5v, boolean enable) throws Throwable {
        FileOutputStream node_3 = null;
        try {
            byte[] open_three = new byte[]{0x33};
            byte[] close = new byte[]{0x36};
            node_3 = new FileOutputStream(node5v);
            node_3.write(enable ? open_three : close);
            Log.v("OtgUtils", "write  success :" + node5v);
        } catch (Throwable e) {
            e.printStackTrace();
        } finally {
            try {
                if (node_3 != null) {
                    node_3.close();
                }
            } catch (Exception e) {
                e.printStackTrace();
            }
        }
    }

    private static boolean isChange(String nodepath_pogo5ven, boolean enable) {

        try {
            if (!TextUtils.isEmpty(nodepath_pogo5ven)) {
                return true;
            }

            Log.v("OtgUtils", "isChange()");

//         String status = new DeviceManager().getSettingProperty("File-"+nodepath_pogo5ven);
//         LogUtils.v("OtgUtils","isChange() status == "+status);

            FileInputStream fileInputStream = new FileInputStream(nodepath_pogo5ven);
            byte[] b = new byte[1024];
            String nodeStr = "";
            //开始读文件
            int len = fileInputStream.read(b);
            if (len > 0) {
                nodeStr = new String(b, 0, len);
            }

            if (enable) {
                for (int i = 0; i < NUM_ENABLE_SIZE; i++) {
                    if (nodeStr.contains(listEnable.get(i))) {
                        Log.v("OtgUtils", "isChange()  already  enable " + "    " + nodepath_pogo5ven + "     [" + nodeStr + "]");
                        return false;//已经包含，说明已经上电，不用再上电
                    }
                }
                Log.v("OtgUtils", "isChange()  not   enable " + "    " + nodepath_pogo5ven + "     [" + nodeStr + "]");
                return true;//没有包含，说明没有上电，需要上电
            } else {
                for (int i = 0; i < NUM_DISABLE_SIZE; i++) {
                    if (nodeStr.contains(listDisable.get(i))) {
                        Log.v("OtgUtils", "isChange()  already  disable " + "    " + nodepath_pogo5ven + "     [" + nodeStr + "]");
                        return false;//已经包含，说明已经下电，不用再下电
                    }
                }
                Log.v("OtgUtils", "isChange()  not  disable " + "    " + nodepath_pogo5ven + "     [" + nodeStr + "]");
                return true;//没有包含，说明没有上电，需要上电
            }
        } catch (IOException e) {
            e.printStackTrace();
            Log.e("OtgUtils", "isChange() " + nodepath_pogo5ven + "   Exception:" + e.getMessage());
        }
        return true;
    }


}

