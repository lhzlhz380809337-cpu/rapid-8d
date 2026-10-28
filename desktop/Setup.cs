using System;
using System.Drawing;
using System.IO;
using System.IO.Compression;
using System.Reflection;
using System.Diagnostics;
using System.Threading.Tasks;
using System.Windows.Forms;
[assembly: AssemblyTitle("Rapid 8D Setup")]
[assembly: AssemblyProduct("Rapid 8D")]
[assembly: AssemblyVersion("0.3.1.0")]
[assembly: AssemblyFileVersion("0.3.1.0")]
class Setup : Form {
    static string destination = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),"Programs","Rapid8D");
    Button install = new Button();
    Label status = new Label();
    ProgressBar progress = new ProgressBar();
    CheckBox launch = new CheckBox();
    bool installing;
    Setup() {
        Text="Rapid 8D 安装";ClientSize=new Size(570,330);StartPosition=FormStartPosition.CenterScreen;FormBorderStyle=FormBorderStyle.FixedDialog;MaximizeBox=false;
        Font=new Font("Microsoft YaHei",10);BackColor=Color.FromArgb(243,246,248);
        var title=new Label(){Text="Rapid 8D",Font=new Font("Microsoft YaHei",25,FontStyle.Bold),Location=new Point(28,22),AutoSize=true,ForeColor=Color.FromArgb(18,51,74)};
        var detail=new Label(){Text="质量问题研析工作台\n引导研析 · 资料成稿 · D4 鱼骨图 · Word / PDF",Location=new Point(30,80),Size=new Size(510,58)};
        var path=new Label(){Text="安装位置（当前用户，无需管理员）\n"+destination,Location=new Point(30,147),Size=new Size(510,48),Font=new Font("Microsoft YaHei",9)};
        status.Text="案例和模型设置单独保存在本机，升级会保留。";status.Location=new Point(30,207);status.Size=new Size(510,28);status.Font=new Font("Microsoft YaHei",9);
        progress.Location=new Point(30,240);progress.Size=new Size(510,8);progress.Style=ProgressBarStyle.Marquee;progress.Visible=false;
        launch.Text="完成后打开 Rapid 8D";launch.Checked=true;launch.Location=new Point(30,272);launch.Size=new Size(240,30);
        install.Text="安装";install.Location=new Point(405,267);install.Size=new Size(135,38);install.BackColor=Color.FromArgb(17,125,131);install.ForeColor=Color.White;install.FlatStyle=FlatStyle.Flat;
        install.Click+=async (s,e)=>{installing=true;install.Enabled=false;progress.Visible=true;status.Text="正在安装，请稍候…";
            try {await Task.Run(()=>Install(destination,true));status.Text="安装完成。桌面快捷方式已创建。";if(launch.Checked)Process.Start(Path.Combine(destination,"Launch Rapid 8D.exe"));install.Text="完成";install.Enabled=true;install.Click+=(ss,ee)=>Close();installing=false;Close();}
            catch(Exception ex){status.Text="安装未完成。";MessageBox.Show(this,ex.Message,"Rapid 8D",MessageBoxButtons.OK,MessageBoxIcon.Error);install.Enabled=true;installing=false;}
            finally{progress.Visible=false;}
        };
        FormClosing+=(s,e)=>{if(installing)e.Cancel=true;};
        Controls.AddRange(new Control[]{title,detail,path,status,progress,launch,install});
    }
    static void Install(string target,bool shortcuts) {
        target=Path.GetFullPath(target).TrimEnd(Path.DirectorySeparatorChar);
        if(target.Length<10 || target==Path.GetPathRoot(target).TrimEnd(Path.DirectorySeparatorChar))throw new Exception("安装路径无效。");
        foreach(var process in Process.GetProcessesByName("Rapid8D")) {
            try {if(Path.GetFullPath(process.MainModule.FileName)==Path.Combine(target,"Rapid8D.exe"))throw new InvalidOperationException("请先关闭已运行的 Rapid 8D，再安装更新。");}
            catch(System.ComponentModel.Win32Exception){}
            finally{process.Dispose();}
        }
        Directory.CreateDirectory(target);
        using(var stream=Assembly.GetExecutingAssembly().GetManifestResourceStream("rapid8d.payload"))
        using(var archive=new ZipArchive(stream,ZipArchiveMode.Read)){
            foreach(var item in archive.Entries){
                string file=Path.GetFullPath(Path.Combine(target,item.FullName.Replace('/',Path.DirectorySeparatorChar)));
                if(!file.StartsWith(target+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase))throw new Exception("安装包内路径无效。");
                if(item.FullName.EndsWith("/")){Directory.CreateDirectory(file);continue;}
                Directory.CreateDirectory(Path.GetDirectoryName(file));
                using(var source=item.Open())
                using(var output=new FileStream(file,FileMode.Create,FileAccess.Write))source.CopyTo(output);
            }
        }
        File.WriteAllText(Path.Combine(target,"安装说明.txt"),"双击 Launch Rapid 8D.exe 启动。\r\n案例与设置保存在 %LOCALAPPDATA%\\Rapid8D。\r\n移动便携版时请保留同目录的 _internal 文件夹。\r\n如需移除程序，关闭后删除安装文件夹和桌面/开始菜单快捷方式；案例目录可单独保留。\r\n",System.Text.Encoding.UTF8);
        if(shortcuts){
            Shortcut(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.DesktopDirectory),"Rapid 8D.lnk"),target);
            Shortcut(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.Programs),"Rapid 8D.lnk"),target);
        }
    }
    static void Shortcut(string path,string target) {
        var type=Type.GetTypeFromProgID("WScript.Shell");var shell=Activator.CreateInstance(type);
        try {
            var shortcut=type.InvokeMember("CreateShortcut",BindingFlags.InvokeMethod,null,shell,new object[]{path});
            try {
                var st=shortcut.GetType();
                string launcher=Path.Combine(target,"Launch Rapid 8D.exe");
                st.InvokeMember("TargetPath",BindingFlags.SetProperty,null,shortcut,new object[]{File.Exists(launcher)?launcher:Path.Combine(target,"Rapid8D.exe")});
                st.InvokeMember("WorkingDirectory",BindingFlags.SetProperty,null,shortcut,new object[]{target});
                st.InvokeMember("Description",BindingFlags.SetProperty,null,shortcut,new object[]{"Rapid 8D 质量问题研析工作台"});
                st.InvokeMember("Save",BindingFlags.InvokeMethod,null,shortcut,null);
            } finally {System.Runtime.InteropServices.Marshal.FinalReleaseComObject(shortcut);}
        } finally {System.Runtime.InteropServices.Marshal.FinalReleaseComObject(shell);}
    }
    [STAThread] static int Main(string[] args) {
        if(args.Length==2 && args[0]=="--extract-only") {
            try{Install(args[1],false);return 0;}catch(Exception ex){File.WriteAllText(Path.Combine(Path.GetTempPath(),"Rapid8D-setup-error.txt"),ex.ToString());return 1;}
        }
        Application.EnableVisualStyles();Application.SetCompatibleTextRenderingDefault(false);Application.Run(new Setup());return 0;
    }
}
