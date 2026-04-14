using System;
using System.Drawing;
using System.Windows.Forms;

namespace UHFDemo
{
    public partial class LogRichTextBox : RichTextBox
    {
        public LogRichTextBox()
        {
            InitializeComponent();
        }

        protected override void OnTextChanged(EventArgs e)
        {
            base.OnTextChanged(e);

            Select(TextLength, 0);
            //ScrollToCaret();
        }

        public void AppendTextEx(string strText, Color clAppend)
        {
            int nLen = TextLength;

            if (nLen != 0)
            {
                AppendText(string.Format("\r\n{0} {1}", DateTime.Now.ToString("yyyy-MM-dd hh:mm:ss.fff"), strText));
                //AppendText(Environment.NewLine + System.DateTime.Now.ToString("yyyy-MM-dd hh:mm:ss.fff") + " " + strText);
            }
            else
            {
                AppendText(string.Format("{0} {1}", DateTime.Now.ToString("yyyy-MM-dd hh:mm:ss.fff"), strText));
                //AppendText(System.DateTime.Now.ToString("yyyy-MM-dd hh:mm:ss.fff") + " " + strText);
            }

            Select(nLen, TextLength - nLen);
            SelectionColor = clAppend;
        }
    }
}
