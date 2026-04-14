namespace UHFDemo
{
    partial class FactoryReset
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            this.groupBox1 = new System.Windows.Forms.GroupBox();
            this.btnFreqCancle = new System.Windows.Forms.Button();
            this.btnFreqSure = new System.Windows.Forms.Button();
            this.rbEurFreq = new System.Windows.Forms.RadioButton();
            this.rbUSFreq = new System.Windows.Forms.RadioButton();
            this.groupBox1.SuspendLayout();
            this.SuspendLayout();
            // 
            // groupBox1
            // 
            this.groupBox1.Controls.Add(this.btnFreqCancle);
            this.groupBox1.Controls.Add(this.btnFreqSure);
            this.groupBox1.Controls.Add(this.rbEurFreq);
            this.groupBox1.Controls.Add(this.rbUSFreq);
            this.groupBox1.Location = new System.Drawing.Point(12, 12);
            this.groupBox1.Name = "groupBox1";
            this.groupBox1.Size = new System.Drawing.Size(482, 157);
            this.groupBox1.TabIndex = 0;
            this.groupBox1.TabStop = false;
            this.groupBox1.Text = "Frequencies Choice";
            // 
            // btnFreqCancle
            // 
            this.btnFreqCancle.Location = new System.Drawing.Point(285, 109);
            this.btnFreqCancle.Name = "btnFreqCancle";
            this.btnFreqCancle.Size = new System.Drawing.Size(75, 23);
            this.btnFreqCancle.TabIndex = 3;
            this.btnFreqCancle.Text = "Cancel";
            this.btnFreqCancle.UseVisualStyleBackColor = true;
            this.btnFreqCancle.Click += new System.EventHandler(this.btnFreqCancle_Click);
            // 
            // btnFreqSure
            // 
            this.btnFreqSure.Location = new System.Drawing.Point(66, 109);
            this.btnFreqSure.Name = "btnFreqSure";
            this.btnFreqSure.Size = new System.Drawing.Size(75, 23);
            this.btnFreqSure.TabIndex = 2;
            this.btnFreqSure.Text = "OK";
            this.btnFreqSure.UseVisualStyleBackColor = true;
            this.btnFreqSure.Click += new System.EventHandler(this.btnFreqSure_Click);
            // 
            // rbEurFreq
            // 
            this.rbEurFreq.AutoSize = true;
            this.rbEurFreq.Location = new System.Drawing.Point(274, 48);
            this.rbEurFreq.Name = "rbEurFreq";
            this.rbEurFreq.Size = new System.Drawing.Size(47, 16);
            this.rbEurFreq.TabIndex = 1;
            this.rbEurFreq.TabStop = true;
            this.rbEurFreq.Text = "ETSI";
            this.rbEurFreq.UseVisualStyleBackColor = true;
            // 
            // rbUSFreq
            // 
            this.rbUSFreq.AutoSize = true;
            this.rbUSFreq.Location = new System.Drawing.Point(66, 49);
            this.rbUSFreq.Name = "rbUSFreq";
            this.rbUSFreq.Size = new System.Drawing.Size(41, 16);
            this.rbUSFreq.TabIndex = 0;
            this.rbUSFreq.TabStop = true;
            this.rbUSFreq.Text = "FCC";
            this.rbUSFreq.UseVisualStyleBackColor = true;
            // 
            // FactoryReset
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 12F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(506, 195);
            this.Controls.Add(this.groupBox1);
            this.Name = "FactoryReset";
            this.StartPosition = System.Windows.Forms.FormStartPosition.CenterScreen;
            this.Text = "Resume Factory Setting";
            this.groupBox1.ResumeLayout(false);
            this.groupBox1.PerformLayout();
            this.ResumeLayout(false);

        }

        #endregion

        private System.Windows.Forms.GroupBox groupBox1;
        private System.Windows.Forms.RadioButton rbEurFreq;
        private System.Windows.Forms.RadioButton rbUSFreq;
        private System.Windows.Forms.Button btnFreqCancle;
        private System.Windows.Forms.Button btnFreqSure;
    }
}