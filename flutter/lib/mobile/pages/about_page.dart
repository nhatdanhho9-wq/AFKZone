import 'package:flutter/material.dart';
import 'package:url_launcher/url_launcher.dart';

class AboutPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Ve AFK Zone'),
        backgroundColor: Colors.deepPurple,
      ),
      body: ListView(
        padding: EdgeInsets.all(16),
        children: [
          // Logo
          Center(
            child: Image.asset(
              'assets/afkzone_logo.png',
              width: 150,
              height: 150,
            ),
          ),
          SizedBox(height: 24),
          
          // App info
          _buildInfoCard(
            'AFK Zone',
            'Phien ban: 2.2.1',
            Icons.info_outline,
            Colors.blue,
          ),
          
          SizedBox(height: 16),
          
          // Description
          _buildSection(
            'Mo ta',
            'AFK Zone la giai phap Remote Desktop hien dai, cho phep ban dieu khien may tinh tu xa mot cach de dang va bao mat.',
          ),
          
          SizedBox(height: 16),
          
          // Credits
          _buildSection(
            'Credits',
            'AFK Zone duoc xay dung tren nen tang RustDesk - mot du an open source tuyet voi.\n\nChung toi chan thanh cam on RustDesk team va cong dong dong gop vien.',
          ),
          
          SizedBox(height: 16),
          
          // Links
          Card(
            child: Column(
              children: [
                _buildLinkTile(
                  'RustDesk GitHub',
                  'https://github.com/rustdesk/rustdesk',
                  Icons.code,
                  Colors.purple,
                ),
                Divider(height: 1),
                _buildLinkTile(
                  'AFK Zone Website',
                  'https://afkzone.cloud',
                  Icons.language,
                  Colors.blue,
                ),
                Divider(height: 1),
                _buildLinkTile(
                  'Chinh sach bao mat',
                  'https://afkzone.cloud/privacy',
                  Icons.privacy_tip,
                  Colors.green,
                ),
                Divider(height: 1),
                _buildLinkTile(
                  'Dieu khoan su dung',
                  'https://afkzone.cloud/terms',
                  Icons.description,
                  Colors.orange,
                ),
              ],
            ),
          ),
          
          SizedBox(height: 16),
          
          // License
          _buildSection(
            'Giay phep',
            'RustDesk Core: AGPL-3.0\nAFK Zone Extensions: Proprietary\n\nSource code: github.com/nhatdanhho9-wq/rustdesk',
          ),
          
          SizedBox(height: 16),
          
          // Contact
          _buildSection(
            'Lien he',
            'Email: nhatdanhho9@gmail.com\nWebsite: afkzone.cloud',
          ),
          
          SizedBox(height: 24),
          
          // Copyright
          Center(
            child: Text(
              '© 2025 AFK Zone\nBuilt on RustDesk',
              textAlign: TextAlign.center,
              style: TextStyle(
                color: Colors.grey[600],
                fontSize: 12,
              ),
            ),
          ),
          
          SizedBox(height: 24),
        ],
      ),
    );
  }
  
  Widget _buildInfoCard(String title, String subtitle, IconData icon, Color color) {
    return Card(
      child: ListTile(
        leading: Icon(icon, color: color, size: 32),
        title: Text(
          title,
          style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold),
        ),
        subtitle: Text(subtitle),
      ),
    );
  }
  
  Widget _buildSection(String title, String content) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              title,
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.bold,
                color: Colors.deepPurple,
              ),
            ),
            SizedBox(height: 8),
            Text(
              content,
              style: TextStyle(fontSize: 14, height: 1.5),
            ),
          ],
        ),
      ),
    );
  }
  
  Widget _buildLinkTile(String title, String url, IconData icon, Color color) {
    return ListTile(
      leading: Icon(icon, color: color),
      title: Text(title),
      trailing: Icon(Icons.open_in_new, size: 18),
      onTap: () async {
        final uri = Uri.parse(url);
        if (await canLaunchUrl(uri)) {
          await launchUrl(uri, mode: LaunchMode.externalApplication);
        }
      },
    );
  }
}

