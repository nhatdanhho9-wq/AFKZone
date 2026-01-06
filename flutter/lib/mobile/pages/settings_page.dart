import 'dart:async';
import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;

import 'package:flutter/material.dart';
import 'package:flutter_hbb/common/widgets/setting_widgets.dart';
import 'package:flutter_hbb/desktop/pages/desktop_setting_page.dart';
import 'package:get/get.dart';
import 'package:provider/provider.dart';
import 'package:settings_ui/settings_ui.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:url_launcher/url_launcher_string.dart';

import '../../common.dart';
import '../../common/widgets/dialog.dart';
import '../../common/widgets/login.dart';
import '../../common/license_service.dart';
import '../../common/auth_service.dart';
import '../../models/model.dart';
import '../../models/platform_model.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/services.dart';
import '../widgets/dialog.dart';
import 'home_page.dart';
import 'scan_page.dart';

class SettingsPage extends StatefulWidget implements PageShape {
  @override
  final title = translate("Settings");

  @override
  final icon = Icon(Icons.settings);

  @override
  final appBarActions = bind.isDisableSettings() ? [] : [ScanButton()];

  @override
  State<SettingsPage> createState() => _SettingsState();
}

enum KeepScreenOn {
  never,
  duringControlled,
  serviceOn,
}

String _keepScreenOnToOption(KeepScreenOn value) {
  switch (value) {
    case KeepScreenOn.never:
      return 'never';
    case KeepScreenOn.duringControlled:
      return 'during-controlled';
    case KeepScreenOn.serviceOn:
      return 'service-on';
  }
}

KeepScreenOn optionToKeepScreenOn(String value) {
  switch (value) {
    case 'never':
      return KeepScreenOn.never;
    case 'service-on':
      return KeepScreenOn.serviceOn;
    default:
      return KeepScreenOn.duringControlled;
  }
}

class _SettingsState extends State<SettingsPage> with WidgetsBindingObserver {
  final _hasIgnoreBattery =
      false; //androidVersion >= 26; // remove because not work on every device
  var _ignoreBatteryOpt = false;
  var _enableStartOnBoot = false;
  var _checkUpdateOnStartup = false;
  var _floatingWindowDisabled = false;
  var _keepScreenOn = KeepScreenOn.duringControlled; // relay on floating window
  var _enableAbr = false;
  var _denyLANDiscovery = false;
  var _onlyWhiteList = false;
  var _enableDirectIPAccess = false;
  var _enableRecordSession = false;
  var _enableHardwareCodec = false;
  var _allowWebSocket = false;
  var _autoRecordIncomingSession = false;
  var _autoRecordOutgoingSession = false;
  var _allowAutoDisconnect = false;
  var _localIP = "";
  var _directAccessPort = "";
  var _fingerprint = "";
  var _buildDate = "";
  var _autoDisconnectTimeout = "";
  var _hideServer = false;
  var _hideProxy = false;
  var _hideNetwork = false;
  var _hideWebSocket = false;
  var _enableTrustedDevices = false;
  var _enableUdpPunch = false;
  var _allowInsecureTlsFallback = false;
  var _disableUdp = false;
  var _enableIpv6Punch = false;
  var _isUsingPublicServer = false;
  var _allowAskForNoteAtEndOfConnection = false;
  String? _licenseKey;
  String? _licenseTier;
  String? _licenseExpiresAt;
  int? _licenseDeviceCount;
  int? _licenseMaxDevices;
  bool _licenseLoading = true;
  bool _logoutLoading = false;
  
  // Developer mode - tap version 7 times to unlock ID/Relay Server settings
  int _versionTapCount = 0;
  bool _developerModeEnabled = false;

  _SettingsState() {
    _enableAbr = option2bool(
        kOptionEnableAbr, bind.mainGetOptionSync(key: kOptionEnableAbr));
    _denyLANDiscovery = !option2bool(kOptionEnableLanDiscovery,
        bind.mainGetOptionSync(key: kOptionEnableLanDiscovery));
    _onlyWhiteList = whitelistNotEmpty();
    _enableDirectIPAccess = option2bool(
        kOptionDirectServer, bind.mainGetOptionSync(key: kOptionDirectServer));
    _enableRecordSession = option2bool(kOptionEnableRecordSession,
        bind.mainGetOptionSync(key: kOptionEnableRecordSession));
    _enableHardwareCodec = option2bool(kOptionEnableHwcodec,
        bind.mainGetOptionSync(key: kOptionEnableHwcodec));
    _allowWebSocket = mainGetBoolOptionSync(kOptionAllowWebSocket);
    _allowInsecureTlsFallback =
        mainGetBoolOptionSync(kOptionAllowInsecureTLSFallback);
    _disableUdp = bind.mainGetOptionSync(key: kOptionDisableUdp) == 'Y';
    _autoRecordIncomingSession = option2bool(kOptionAllowAutoRecordIncoming,
        bind.mainGetOptionSync(key: kOptionAllowAutoRecordIncoming));
    _autoRecordOutgoingSession = option2bool(kOptionAllowAutoRecordOutgoing,
        bind.mainGetLocalOption(key: kOptionAllowAutoRecordOutgoing));
    _localIP = bind.mainGetOptionSync(key: 'local-ip-addr');
    _directAccessPort = bind.mainGetOptionSync(key: kOptionDirectAccessPort);
    _allowAutoDisconnect = option2bool(kOptionAllowAutoDisconnect,
        bind.mainGetOptionSync(key: kOptionAllowAutoDisconnect));
    _autoDisconnectTimeout =
        bind.mainGetOptionSync(key: kOptionAutoDisconnectTimeout);
    _hideServer =
        bind.mainGetBuildinOption(key: kOptionHideServerSetting) == 'Y';
    _hideProxy = bind.mainGetBuildinOption(key: kOptionHideProxySetting) == 'Y';
    _hideNetwork =
        bind.mainGetBuildinOption(key: kOptionHideNetworkSetting) == 'Y';
    _hideWebSocket =
        bind.mainGetBuildinOption(key: kOptionHideWebSocketSetting) == 'Y' ||
            isWeb;
    _enableTrustedDevices = mainGetBoolOptionSync(kOptionEnableTrustedDevices);
    _enableUdpPunch = mainGetLocalBoolOptionSync(kOptionEnableUdpPunch);
    _enableIpv6Punch = mainGetLocalBoolOptionSync(kOptionEnableIpv6Punch);
    _allowAskForNoteAtEndOfConnection =
        mainGetLocalBoolOptionSync(kOptionAllowAskForNoteAtEndOfConnection);
  }

  @override
  void initState() {
    super.initState();
    _loadLicenseInfo();
    WidgetsBinding.instance.addObserver(this);

    WidgetsBinding.instance.addPostFrameCallback((_) async {
      var update = false;

      if (_hasIgnoreBattery) {
        if (await checkAndUpdateIgnoreBatteryStatus()) {
          update = true;
        }
      }

      if (await checkAndUpdateStartOnBoot()) {
        update = true;
      }

      // start on boot depends on ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS and SYSTEM_ALERT_WINDOW
      var enableStartOnBoot =
          await gFFI.invokeMethod(AndroidChannel.kGetStartOnBootOpt);
      if (enableStartOnBoot) {
        if (!await canStartOnBoot()) {
          enableStartOnBoot = false;
          gFFI.invokeMethod(AndroidChannel.kSetStartOnBootOpt, false);
        }
      }

      if (enableStartOnBoot != _enableStartOnBoot) {
        update = true;
        _enableStartOnBoot = enableStartOnBoot;
      }

      var checkUpdateOnStartup =
          mainGetLocalBoolOptionSync(kOptionEnableCheckUpdate);
      if (checkUpdateOnStartup != _checkUpdateOnStartup) {
        update = true;
        _checkUpdateOnStartup = checkUpdateOnStartup;
      }

      var floatingWindowDisabled =
          bind.mainGetLocalOption(key: kOptionDisableFloatingWindow) == "Y" ||
              !await AndroidPermissionManager.check(kSystemAlertWindow);
      if (floatingWindowDisabled != _floatingWindowDisabled) {
        update = true;
        _floatingWindowDisabled = floatingWindowDisabled;
      }

      final keepScreenOn = _floatingWindowDisabled
          ? KeepScreenOn.never
          : optionToKeepScreenOn(
              bind.mainGetLocalOption(key: kOptionKeepScreenOn));
      if (keepScreenOn != _keepScreenOn) {
        update = true;
        _keepScreenOn = keepScreenOn;
      }

      final fingerprint = await bind.mainGetFingerprint();
      if (_fingerprint != fingerprint) {
        update = true;
        _fingerprint = fingerprint;
      }

      final buildDate = await bind.mainGetBuildDate();
      if (_buildDate != buildDate) {
        update = true;
        _buildDate = buildDate;
      }

      final isUsingPublicServer = await bind.mainIsUsingPublicServer();
      if (_isUsingPublicServer != isUsingPublicServer) {
        update = true;
        _isUsingPublicServer = isUsingPublicServer;
      }

      if (update) {
        setState(() {});
      }
    });
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      () async {
        final ibs = await checkAndUpdateIgnoreBatteryStatus();
        final sob = await checkAndUpdateStartOnBoot();
        if (ibs || sob) {
          setState(() {});
        }
      }();
    }
  }

  Future<bool> checkAndUpdateIgnoreBatteryStatus() async {
    final res = await AndroidPermissionManager.check(
        kRequestIgnoreBatteryOptimizations);
    if (_ignoreBatteryOpt != res) {
      _ignoreBatteryOpt = res;
      return true;
    } else {
      return false;
    }
  }

  Future<bool> checkAndUpdateStartOnBoot() async {
    if (!await canStartOnBoot() && _enableStartOnBoot) {
      _enableStartOnBoot = false;
      debugPrint(
          "checkAndUpdateStartOnBoot and set _enableStartOnBoot -> false");
      gFFI.invokeMethod(AndroidChannel.kSetStartOnBootOpt, false);
      return true;
    } else {
      return false;
    }
  }

  Future<void> _loadLicenseInfo() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final licenseKey = prefs.getString('license_key');
      final expiresAt = prefs.getInt('afk_license_expires_at');
      
      if (licenseKey != null) {
        // Get license details from check API
        final deviceId = await LicenseService.getDeviceFingerprint();
        final result = await LicenseService.checkLicense(licenseKey, deviceId);
        
        // Get license info including device count
        final licenseInfo = await LicenseService.getLicenseInfo(licenseKey);
        
        setState(() {
          _licenseKey = licenseKey;
          if (result != null) {
            _licenseTier = result['tier']?.toString();
            _licenseMaxDevices = result['max_devices'] as int?;
            if (expiresAt != null) {
              final date = DateTime.fromMillisecondsSinceEpoch(expiresAt);
              _licenseExpiresAt = '${date.day}/${date.month}/${date.year}';
            }
          }
          if (licenseInfo != null) {
            _licenseDeviceCount = licenseInfo['device_count'] as int?;
            _licenseMaxDevices = licenseInfo['max_devices'] as int?;
          }
          _licenseLoading = false;
        });
      } else {
        setState(() {
          _licenseLoading = false;
        });
      }
    } catch (e) {
      print('Error loading license info: $e');
      setState(() {
        _licenseLoading = false;
      });
    }
  }

  Future<void> _logoutLicense() async {
    if (_logoutLoading) return;
    
    // Show confirmation dialog
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Xác nhận đăng xuất'),
        content: Text('Bạn có chắc chắn muốn đăng xuất license?\n\nThiết bị này sẽ bị xóa khỏi danh sách thiết bị đã kích hoạt và bạn sẽ phải nhập lại license key để sử dụng.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(false),
            child: Text('Hủy'),
          ),
          TextButton(
            onPressed: () => Navigator.of(context).pop(true),
            style: TextButton.styleFrom(foregroundColor: Colors.red),
            child: Text('Đăng xuất'),
          ),
        ],
      ),
    );
    
    if (confirm != true) return;
    
    setState(() {
      _logoutLoading = true;
    });
    
    try {
      final prefs = await SharedPreferences.getInstance();
      final licenseKey = prefs.getString('license_key');
      final deviceId = await LicenseService.getDeviceFingerprint();
      
      // Call API to remove device from database
      if (licenseKey != null) {
        await LicenseService.logoutDevice(licenseKey, deviceId);
      }
      
      // Clear local license data
      await prefs.remove('license_key');
      await prefs.remove('device_id');
      await prefs.remove('afk_license_active');
      await prefs.remove('afk_license_expires_at');
      await prefs.remove('id_server');
      await prefs.remove('relay_server');
      await prefs.remove('api_server');
      await prefs.remove('public_key');
      
      // Clear server settings
      await bind.mainSetOption(key: 'custom-rendezvous-server', value: '');
      await bind.mainSetOption(key: 'relay-server', value: '');
      await bind.mainSetOption(key: 'api-server', value: '');
      await bind.mainSetOption(key: 'key', value: '');
      
      setState(() {
        _licenseKey = null;
        _licenseTier = null;
        _licenseExpiresAt = null;
        _licenseDeviceCount = null;
        _licenseMaxDevices = null;
        _logoutLoading = false;
      });
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Đã đăng xuất license thành công'),
          backgroundColor: Colors.green,
        ),
      );
      
      // Navigate back to license activation screen
      Navigator.of(context).pushNamedAndRemoveUntil('/', (route) => false);
    } catch (e) {
      print('Error logging out license: $e');
      setState(() {
        _logoutLoading = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Lỗi khi đăng xuất: ${e.toString()}'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  void _showDeviceAliasDialog() async {
    final prefs = await SharedPreferences.getInstance();
    final currentAlias = prefs.getString('device_alias') ?? '';
    final controller = TextEditingController(text: currentAlias);
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            Icon(Icons.edit, color: Colors.blue),
            SizedBox(width: 8),
            Text('Đặt tên thiết bị'),
          ],
        ),
        content: TextField(
          controller: controller,
          decoration: InputDecoration(
            labelText: 'Alias',
            hintText: 'Ví dụ: Điện thoại công việc',
            border: OutlineInputBorder(),
          ),
          autofocus: true,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Hủy'),
          ),
          ElevatedButton(
            onPressed: () async {
              final newAlias = controller.text.trim();
              await prefs.setString('device_alias', newAlias);
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Đã lưu tên thiết bị: $newAlias')),
              );
            },
            child: Text('Lưu'),
          ),
        ],
      ),
    );
  }

  void _showRegionSwitchDialog() {
    showDialog(
      context: context,
      builder: (context) => _RegionSwitchDialogContent(onApply: _applyRegion),
    );
  }

  void _applyRegion(Map<String, dynamic> region) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('selected_region', region['code'] ?? 'vietnam');
    await prefs.setString('id_server', region['id_server'] ?? 'id.afkzone.cloud');
    await prefs.setString('relay_server', region['relay_server'] ?? 'id.afkzone.cloud');
    
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Đã chọn vùng'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.check_circle, color: Colors.green, size: 48),
            SizedBox(height: 12),
            Text('Vùng máy chủ: ${region['name'] ?? region['code']}'),
            SizedBox(height: 8),
            Text(
              'Khởi động lại ứng dụng để áp dụng thay đổi.',
              style: TextStyle(fontSize: 13, color: Colors.grey[600]),
              textAlign: TextAlign.center,
            ),
          ],
        ),
        actions: [
          ElevatedButton(
            onPressed: () => Navigator.pop(context),
            child: Text('OK'),
          ),
        ],
      ),
    );
  }

  // Device Management - Assign License
  void _showAssignLicenseDialog() {
    final deviceIdController = TextEditingController();
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [Icon(Icons.devices, color: Colors.blue), SizedBox(width: 8), Text('Gán License')],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Nhập Device ID của thiết bị muốn gán:', style: TextStyle(fontWeight: FontWeight.w500)),
            SizedBox(height: 12),
            TextField(
              controller: deviceIdController,
              decoration: InputDecoration(
                labelText: 'Device ID',
                hintText: 'abc123def456...',
                border: OutlineInputBorder(),
                prefixIcon: Icon(Icons.perm_device_information),
              ),
            ),
            SizedBox(height: 12),
            Container(
              padding: EdgeInsets.all(10),
              decoration: BoxDecoration(color: Colors.blue.shade50, borderRadius: BorderRadius.circular(8)),
              child: Row(
                children: [
                  Icon(Icons.info_outline, size: 16, color: Colors.blue),
                  SizedBox(width: 8),
                  Expanded(child: Text('Device ID lấy từ Settings → Thiết bị này', style: TextStyle(fontSize: 12, color: Colors.blue.shade800))),
                ],
              ),
            ),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: Text('Hủy')),
          ElevatedButton(
            onPressed: () async {
              final targetDeviceId = deviceIdController.text.trim();
              if (targetDeviceId.isEmpty) {
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Vui lòng nhập Device ID')));
                return;
              }
              Navigator.pop(context);
              _assignLicenseToDevice(targetDeviceId);
            },
            child: Text('Gán License'),
          ),
        ],
      ),
    );
  }

  Future<void> _assignLicenseToDevice(String targetDeviceId) async {
    try {
      // D9 fix: Backend requires device_id (current) + target_device_id
      final prefs = await SharedPreferences.getInstance();
      final currentDeviceId = prefs.getString('device_id') ?? '';
      
      final response = await http.post(
        Uri.parse('https://api.afkzone.cloud/api/license/assign'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({
          'license_key': _licenseKey,
          'device_id': currentDeviceId,        // Current device (D9 fix)
          'target_device_id': targetDeviceId,  // Target device to assign to
        }),
      ).timeout(Duration(seconds: 10));
      
      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('✅ Đã gán license thành công!'), backgroundColor: Colors.green));
      } else {
        final data = json.decode(response.body);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('❌ ${data['detail'] ?? 'Lỗi gán license'}'), backgroundColor: Colors.red));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('❌ Lỗi kết nối: $e'), backgroundColor: Colors.red));
    }
  }

  // Device Management - View Device List  
  void _showDeviceListDialog() {
    showDialog(
      context: context,
      builder: (context) => _DeviceListDialogContent(licenseKey: _licenseKey ?? ''),
    );
  }

  @override
  Widget build(BuildContext context) {
    Provider.of<FfiModel>(context);
    final outgoingOnly = bind.isOutgoingOnly();
    final incomingOnly = bind.isIncomingOnly();
    final customClientSection = CustomSettingsSection(
        child: Column(
      children: [
        if (bind.isCustomClient())
          Align(
            alignment: Alignment.center,
            child: loadPowered(context),
          ),
        Align(
          alignment: Alignment.center,
          child: loadLogo(),
        )
      ],
    ));
    final List<AbstractSettingsTile> enhancementsTiles = [];
    final enable2fa = bind.mainHasValid2FaSync();
    final List<AbstractSettingsTile> tfaTiles = [
      SettingsTile.switchTile(
        title: Text(translate('enable-2fa-title')),
        initialValue: enable2fa,
        onToggle: (v) async {
          update() async {
            setState(() {});
          }

          if (v == false) {
            CommonConfirmDialog(
                gFFI.dialogManager, translate('cancel-2fa-confirm-tip'), () {
              change2fa(callback: update);
            });
          } else {
            change2fa(callback: update);
          }
        },
      ),
      if (enable2fa)
        SettingsTile.switchTile(
          title: Text(translate('Telegram bot')),
          initialValue: bind.mainHasValidBotSync(),
          onToggle: (v) async {
            update() async {
              setState(() {});
            }

            if (v == false) {
              CommonConfirmDialog(
                  gFFI.dialogManager, translate('cancel-bot-confirm-tip'), () {
                changeBot(callback: update);
              });
            } else {
              changeBot(callback: update);
            }
          },
        ),
      if (enable2fa)
        SettingsTile.switchTile(
          title: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(translate('Enable trusted devices')),
              Text('* ${translate('enable-trusted-devices-tip')}',
                  style: Theme.of(context).textTheme.bodySmall),
            ],
          ),
          initialValue: _enableTrustedDevices,
          onToggle: isOptionFixed(kOptionEnableTrustedDevices)
              ? null
              : (v) async {
                  mainSetBoolOption(kOptionEnableTrustedDevices, v);
                  setState(() {
                    _enableTrustedDevices = v;
                  });
                },
        ),
      if (enable2fa && _enableTrustedDevices)
        SettingsTile(
            title: Text(translate('Manage trusted devices')),
            trailing: Icon(Icons.arrow_forward_ios),
            onPressed: (context) {
              Navigator.push(context, MaterialPageRoute(builder: (context) {
                return _ManageTrustedDevices();
              }));
            })
    ];
    final List<AbstractSettingsTile> shareScreenTiles = [
      SettingsTile.switchTile(
        title: Text(translate('Deny LAN discovery')),
        initialValue: _denyLANDiscovery,
        onToggle: isOptionFixed(kOptionEnableLanDiscovery)
            ? null
            : (v) async {
                await bind.mainSetOption(
                    key: kOptionEnableLanDiscovery,
                    value: bool2option(kOptionEnableLanDiscovery, !v));
                final newValue = !option2bool(kOptionEnableLanDiscovery,
                    await bind.mainGetOption(key: kOptionEnableLanDiscovery));
                setState(() {
                  _denyLANDiscovery = newValue;
                });
              },
      ),
      SettingsTile.switchTile(
        title: Row(children: [
          Expanded(child: Text(translate('Use IP Whitelisting'))),
          Offstage(
                  offstage: !_onlyWhiteList,
                  child: const Icon(Icons.warning_amber_rounded,
                      color: Color.fromARGB(255, 255, 204, 0)))
              .marginOnly(left: 5)
        ]),
        initialValue: _onlyWhiteList,
        onToggle: (_) async {
          update() async {
            final onlyWhiteList = whitelistNotEmpty();
            if (onlyWhiteList != _onlyWhiteList) {
              setState(() {
                _onlyWhiteList = onlyWhiteList;
              });
            }
          }

          changeWhiteList(callback: update);
        },
      ),
      SettingsTile.switchTile(
        title: Text(translate('Adaptive bitrate')),
        initialValue: _enableAbr,
        onToggle: isOptionFixed(kOptionEnableAbr)
            ? null
            : (v) async {
                await mainSetBoolOption(kOptionEnableAbr, v);
                final newValue = await mainGetBoolOption(kOptionEnableAbr);
                setState(() {
                  _enableAbr = newValue;
                });
              },
      ),
      SettingsTile.switchTile(
        title: Text(translate('Enable recording session')),
        initialValue: _enableRecordSession,
        onToggle: isOptionFixed(kOptionEnableRecordSession)
            ? null
            : (v) async {
                await mainSetBoolOption(kOptionEnableRecordSession, v);
                final newValue =
                    await mainGetBoolOption(kOptionEnableRecordSession);
                setState(() {
                  _enableRecordSession = newValue;
                });
              },
      ),
      SettingsTile.switchTile(
        title: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Expanded(
                  child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                    Text(translate("Direct IP Access")),
                    Offstage(
                        offstage: !_enableDirectIPAccess,
                        child: Text(
                          '${translate("Local Address")}: $_localIP${_directAccessPort.isEmpty ? "" : ":$_directAccessPort"}',
                          style: Theme.of(context).textTheme.bodySmall,
                        )),
                  ])),
              Offstage(
                  offstage: !_enableDirectIPAccess,
                  child: IconButton(
                      padding: EdgeInsets.zero,
                      icon: Icon(
                        Icons.edit,
                        size: 20,
                      ),
                      onPressed: isOptionFixed(kOptionDirectAccessPort)
                          ? null
                          : () async {
                              final port = await changeDirectAccessPort(
                                  _localIP, _directAccessPort);
                              setState(() {
                                _directAccessPort = port;
                              });
                            }))
            ]),
        initialValue: _enableDirectIPAccess,
        onToggle: isOptionFixed(kOptionDirectServer)
            ? null
            : (_) async {
                _enableDirectIPAccess = !_enableDirectIPAccess;
                String value =
                    bool2option(kOptionDirectServer, _enableDirectIPAccess);
                await bind.mainSetOption(
                    key: kOptionDirectServer, value: value);
                setState(() {});
              },
      ),
      SettingsTile.switchTile(
        title: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Expanded(
                  child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                    Text(translate("auto_disconnect_option_tip")),
                    Offstage(
                        offstage: !_allowAutoDisconnect,
                        child: Text(
                          '${_autoDisconnectTimeout.isEmpty ? '10' : _autoDisconnectTimeout} min',
                          style: Theme.of(context).textTheme.bodySmall,
                        )),
                  ])),
              Offstage(
                  offstage: !_allowAutoDisconnect,
                  child: IconButton(
                      padding: EdgeInsets.zero,
                      icon: Icon(
                        Icons.edit,
                        size: 20,
                      ),
                      onPressed: isOptionFixed(kOptionAutoDisconnectTimeout)
                          ? null
                          : () async {
                              final timeout = await changeAutoDisconnectTimeout(
                                  _autoDisconnectTimeout);
                              setState(() {
                                _autoDisconnectTimeout = timeout;
                              });
                            }))
            ]),
        initialValue: _allowAutoDisconnect,
        onToggle: isOptionFixed(kOptionAllowAutoDisconnect)
            ? null
            : (_) async {
                _allowAutoDisconnect = !_allowAutoDisconnect;
                String value = bool2option(
                    kOptionAllowAutoDisconnect, _allowAutoDisconnect);
                await bind.mainSetOption(
                    key: kOptionAllowAutoDisconnect, value: value);
                setState(() {});
              },
      )
    ];
    if (_hasIgnoreBattery) {
      enhancementsTiles.insert(
          0,
          SettingsTile.switchTile(
              initialValue: _ignoreBatteryOpt,
              title: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(translate('Keep AFK Zone background service')),
                    Text('* ${translate('Ignore Battery Optimizations')}',
                        style: Theme.of(context).textTheme.bodySmall),
                  ]),
              onToggle: (v) async {
                if (v) {
                  await AndroidPermissionManager.request(
                      kRequestIgnoreBatteryOptimizations);
                } else {
                  final res = await gFFI.dialogManager.show<bool>(
                      (setState, close, context) => CustomAlertDialog(
                            title: Text(translate("Open System Setting")),
                            content: Text(translate(
                                "android_open_battery_optimizations_tip")),
                            actions: [
                              dialogButton("Cancel",
                                  onPressed: () => close(), isOutline: true),
                              dialogButton(
                                "Open System Setting",
                                onPressed: () => close(true),
                              ),
                            ],
                          ));
                  if (res == true) {
                    AndroidPermissionManager.startAction(
                        kActionApplicationDetailsSettings);
                  }
                }
              }));
    }
    enhancementsTiles.add(SettingsTile.switchTile(
        initialValue: _enableStartOnBoot,
        title: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(translate('Start on boot')),
          Text(
              '* ${translate('Start the screen sharing service on boot, requires special permissions')}',
              style: Theme.of(context).textTheme.bodySmall),
        ]),
        onToggle: (toValue) async {
          if (toValue) {
            // 1. request kIgnoreBatteryOptimizations
            if (!await AndroidPermissionManager.check(
                kRequestIgnoreBatteryOptimizations)) {
              if (!await AndroidPermissionManager.request(
                  kRequestIgnoreBatteryOptimizations)) {
                return;
              }
            }

            // 2. request kSystemAlertWindow
            if (!await AndroidPermissionManager.check(kSystemAlertWindow)) {
              if (!await AndroidPermissionManager.request(kSystemAlertWindow)) {
                return;
              }
            }

            // (Optional) 3. request input permission
          }
          setState(() => _enableStartOnBoot = toValue);

          gFFI.invokeMethod(AndroidChannel.kSetStartOnBootOpt, toValue);
        }));

    if (!bind.isCustomClient()) {
      enhancementsTiles.add(
        SettingsTile.switchTile(
          initialValue: _checkUpdateOnStartup,
          title:
              Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(translate('Check for software update on startup')),
          ]),
          onToggle: (bool toValue) async {
            await mainSetLocalBoolOption(kOptionEnableCheckUpdate, toValue);
            setState(() => _checkUpdateOnStartup = toValue);
          },
        ),
      );
    }

    onFloatingWindowChanged(bool toValue) async {
      if (toValue) {
        if (!await AndroidPermissionManager.check(kSystemAlertWindow)) {
          if (!await AndroidPermissionManager.request(kSystemAlertWindow)) {
            return;
          }
        }
      }
      final disable = !toValue;
      bind.mainSetLocalOption(
          key: kOptionDisableFloatingWindow,
          value: disable ? 'Y' : defaultOptionNo);
      setState(() => _floatingWindowDisabled = disable);
      gFFI.serverModel.androidUpdatekeepScreenOn();
    }

    enhancementsTiles.add(SettingsTile.switchTile(
        initialValue: !_floatingWindowDisabled,
        title: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(translate('Floating window')),
          Text('* ${translate('floating_window_tip')}',
              style: Theme.of(context).textTheme.bodySmall),
        ]),
        onToggle: bind.mainIsOptionFixed(key: kOptionDisableFloatingWindow)
            ? null
            : onFloatingWindowChanged));

    enhancementsTiles.add(_getPopupDialogRadioEntry(
      title: 'Keep screen on',
      list: [
        _RadioEntry('Never', _keepScreenOnToOption(KeepScreenOn.never)),
        _RadioEntry('During controlled',
            _keepScreenOnToOption(KeepScreenOn.duringControlled)),
        _RadioEntry('During service is on',
            _keepScreenOnToOption(KeepScreenOn.serviceOn)),
      ],
      getter: () => _keepScreenOnToOption(_floatingWindowDisabled
          ? KeepScreenOn.never
          : optionToKeepScreenOn(
              bind.mainGetLocalOption(key: kOptionKeepScreenOn))),
      asyncSetter: isOptionFixed(kOptionKeepScreenOn) || _floatingWindowDisabled
          ? null
          : (value) async {
              await bind.mainSetLocalOption(
                  key: kOptionKeepScreenOn, value: value);
              setState(() => _keepScreenOn = optionToKeepScreenOn(value));
              gFFI.serverModel.androidUpdatekeepScreenOn();
            },
    ));

    final disabledSettings = bind.isDisableSettings();
    final hideSecuritySettings =
        bind.mainGetBuildinOption(key: kOptionHideSecuritySetting) == 'Y';
    final settings = SettingsList(
      sections: [
        customClientSection,
        // License Info Section (replaces Account/Login)
        SettingsSection(
          title: Text('Thông tin License'),
          tiles: [
            if (_licenseLoading)
              SettingsTile(
                title: Text('Đang tải...'),
                leading: SizedBox(
                  width: 24,
                  height: 24,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
              )
            else if (_licenseKey != null) ...[
              SettingsTile(
                title: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('License Key:', style: TextStyle(fontSize: 12, color: Colors.grey)),
                    SizedBox(height: 4),
                    SelectableText(_licenseKey!, style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold)),
                    if (_licenseTier != null) ...[
                      SizedBox(height: 8),
                      Text('Gói: ${_licenseTier!.toUpperCase()}', style: TextStyle(fontSize: 12)),
                    ],
                    if (_licenseExpiresAt != null) ...[
                      SizedBox(height: 4),
                      Text('Hết hạn: $_licenseExpiresAt', style: TextStyle(fontSize: 12)),
                    ],
                    // Device count info
                    SizedBox(height: 8),
                    Row(
                      children: [
                        Icon(Icons.devices, size: 16, color: Colors.grey),
                        SizedBox(width: 4),
                        Text(
                          'Thiết bị: ${_licenseDeviceCount ?? '...'} / ${_licenseMaxDevices == -1 ? 'Không giới hạn' : (_licenseMaxDevices?.toString() ?? '...')}',
                          style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                        ),
                      ],
                    ),
                  ],
                ),
                leading: Icon(Icons.vpn_key, color: Colors.green),
                trailing: IconButton(
                  icon: Icon(Icons.copy),
                  onPressed: () async {
                    if (_licenseKey != null) {
                      await Clipboard.setData(ClipboardData(text: _licenseKey!));
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Đã copy license key')),
                      );
                    }
                  },
                ),
              ),
              // Logout button
              SettingsTile(
                title: Text(
                  'Đăng xuất License',
                  style: TextStyle(color: Colors.red),
                ),
                description: Text('Xóa thiết bị này khỏi license'),
                leading: _logoutLoading 
                  ? SizedBox(
                      width: 24,
                      height: 24,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.red),
                    )
                  : Icon(Icons.logout, color: Colors.red),
                onPressed: _logoutLoading ? null : (context) => _logoutLicense(),
              ),
            ] else
              SettingsTile(
                title: Text('Chưa có license'),
                leading: Icon(Icons.warning, color: Colors.orange),
              ),
          ],
        ),
        // Device ID & Alias Section (Feature 5)
        SettingsSection(
          title: Text('Thiết bị này'),
          tiles: [
            SettingsTile(
              title: FutureBuilder<String>(
                future: LicenseService.getDeviceFingerprint(),
                builder: (context, snapshot) {
                  final deviceId = snapshot.data ?? 'Đang tải...';
                  return Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Device ID:', style: TextStyle(fontSize: 12, color: Colors.grey)),
                      SizedBox(height: 4),
                      SelectableText(
                        deviceId,
                        style: TextStyle(fontSize: 12, fontFamily: 'monospace'),
                      ),
                    ],
                  );
                },
              ),
              leading: Icon(Icons.perm_device_information),
              trailing: IconButton(
                icon: Icon(Icons.copy, size: 20),
                onPressed: () async {
                  final deviceId = await LicenseService.getDeviceFingerprint();
                  await Clipboard.setData(ClipboardData(text: deviceId));
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(content: Text('Đã copy Device ID')),
                  );
                },
              ),
            ),
            SettingsTile(
              title: Text('Đặt tên thiết bị'),
              description: Text('Đặt alias để dễ nhận diện'),
              leading: Icon(Icons.edit),
              onPressed: (context) => _showDeviceAliasDialog(),
            ),
          ],
        ),
        // Region Switch Section (Feature 6)
        SettingsSection(
          title: Text('Máy chủ'),
          tiles: [
            SettingsTile(
              title: Text('Chọn vùng máy chủ'),
              description: Text('Cài đặt server region'),
              leading: Icon(Icons.public),
              onPressed: (context) => _showRegionSwitchDialog(),
            ),
          ],
        ),
        // License Manager Section (Feature D - Device Management)
        if (_licenseKey != null)
          SettingsSection(
            title: Text('Quản lý thiết bị'),
            tiles: [
              SettingsTile(
                title: Text('Gán license cho thiết bị khác'),
                description: Text('Nhập device_id thủ công'),
                leading: Icon(Icons.devices, color: Colors.blue),
                onPressed: (context) => _showAssignLicenseDialog(),
              ),
              SettingsTile(
                title: Text('Xem thiết bị đã kích hoạt'),
                description: Text('Danh sách device + gỡ device'),
                leading: Icon(Icons.list_alt, color: Colors.green),
                onPressed: (context) => _showDeviceListDialog(),
              ),
            ],
          ),
        SettingsSection(title: Text(translate("Settings")), tiles: [
          // ID/Relay Server settings - hidden by default, show only in developer mode
          // Tap Version 7 times to enable developer mode
          if (_developerModeEnabled && !disabledSettings && !_hideNetwork && !_hideServer)
            SettingsTile(
                title: Text(translate('ID/Relay Server')),
                description: Text('Developer Mode', style: TextStyle(color: Colors.orange, fontSize: 10)),
                leading: Icon(Icons.cloud, color: Colors.orange),
                onPressed: (context) {
                  showServerSettings(gFFI.dialogManager, (callback) async {
                    _isUsingPublicServer = await bind.mainIsUsingPublicServer();
                    setState(callback);
                  });
                }),
          if (!_hideNetwork && !_hideProxy)
            SettingsTile(
                title: Text(translate('Socks5/Http(s) Proxy')),
                leading: Icon(Icons.network_ping),
                onPressed: (context) {
                  changeSocks5Proxy();
                }),
          if (!disabledSettings && !_hideNetwork && !_hideWebSocket)
            SettingsTile.switchTile(
              title: Text(translate('Use WebSocket')),
              initialValue: _allowWebSocket,
              onToggle: isOptionFixed(kOptionAllowWebSocket)
                  ? null
                  : (v) async {
                      await mainSetBoolOption(kOptionAllowWebSocket, v);
                      final newValue =
                          await mainGetBoolOption(kOptionAllowWebSocket);
                      setState(() {
                        _allowWebSocket = newValue;
                      });
                    },
            ),
          if (!_isUsingPublicServer)
            SettingsTile.switchTile(
              title: Text(translate('Allow insecure TLS fallback')),
              initialValue: _allowInsecureTlsFallback,
              onToggle: isOptionFixed(kOptionAllowInsecureTLSFallback)
                  ? null
                  : (v) async {
                      await mainSetBoolOption(
                          kOptionAllowInsecureTLSFallback, v);
                      final newValue = mainGetBoolOptionSync(
                          kOptionAllowInsecureTLSFallback);
                      setState(() {
                        _allowInsecureTlsFallback = newValue;
                      });
                    },
            ),
          if (isAndroid && !outgoingOnly && !_isUsingPublicServer)
            SettingsTile.switchTile(
              title: Text(translate('Disable UDP')),
              initialValue: _disableUdp,
              onToggle: isOptionFixed(kOptionDisableUdp)
                  ? null
                  : (v) async {
                      await bind.mainSetOption(
                          key: kOptionDisableUdp, value: v ? 'Y' : 'N');
                      final newValue =
                          bind.mainGetOptionSync(key: kOptionDisableUdp) == 'Y';
                      setState(() {
                        _disableUdp = newValue;
                      });
                    },
            ),
          if (!incomingOnly)
            SettingsTile.switchTile(
              title: Text(translate('Enable UDP hole punching')),
              initialValue: _enableUdpPunch,
              onToggle: (v) async {
                await mainSetLocalBoolOption(kOptionEnableUdpPunch, v);
                final newValue =
                    mainGetLocalBoolOptionSync(kOptionEnableUdpPunch);
                setState(() {
                  _enableUdpPunch = newValue;
                });
              },
            ),
          if (!incomingOnly)
            SettingsTile.switchTile(
              title: Text(translate('Enable IPv6 P2P connection')),
              initialValue: _enableIpv6Punch,
              onToggle: (v) async {
                await mainSetLocalBoolOption(kOptionEnableIpv6Punch, v);
                final newValue =
                    mainGetLocalBoolOptionSync(kOptionEnableIpv6Punch);
                setState(() {
                  _enableIpv6Punch = newValue;
                });
              },
            ),
          SettingsTile(
              title: Text(translate('Language')),
              leading: Icon(Icons.translate),
              onPressed: (context) {
                showLanguageSettings(gFFI.dialogManager);
              }),
          SettingsTile(
            title: Text(translate(
                Theme.of(context).brightness == Brightness.light
                    ? 'Light Theme'
                    : 'Dark Theme')),
            leading: Icon(Theme.of(context).brightness == Brightness.light
                ? Icons.dark_mode
                : Icons.light_mode),
            onPressed: (context) {
              showThemeSettings(gFFI.dialogManager);
            },
          ),
          if (!bind.isDisableAccount())
            SettingsTile.switchTile(
              title: Text(translate('note-at-conn-end-tip')),
              initialValue: _allowAskForNoteAtEndOfConnection,
              onToggle: (v) async {
                if (v && !gFFI.userModel.isLogin) {
                  final res = await loginDialog();
                  if (res != true) return;
                }
                await mainSetLocalBoolOption(
                    kOptionAllowAskForNoteAtEndOfConnection, v);
                final newValue = mainGetLocalBoolOptionSync(
                    kOptionAllowAskForNoteAtEndOfConnection);
                setState(() {
                  _allowAskForNoteAtEndOfConnection = newValue;
                });
              },
            )
        ]),
        if (isAndroid)
          SettingsSection(title: Text(translate('Hardware Codec')), tiles: [
            SettingsTile.switchTile(
              title: Text(translate('Enable hardware codec')),
              initialValue: _enableHardwareCodec,
              onToggle: isOptionFixed(kOptionEnableHwcodec)
                  ? null
                  : (v) async {
                      await mainSetBoolOption(kOptionEnableHwcodec, v);
                      final newValue =
                          await mainGetBoolOption(kOptionEnableHwcodec);
                      setState(() {
                        _enableHardwareCodec = newValue;
                      });
                    },
            ),
          ]),
        if (isAndroid)
          SettingsSection(
            title: Text(translate("Recording")),
            tiles: [
              if (!outgoingOnly)
                SettingsTile.switchTile(
                  title:
                      Text(translate('Automatically record incoming sessions')),
                  initialValue: _autoRecordIncomingSession,
                  onToggle: isOptionFixed(kOptionAllowAutoRecordIncoming)
                      ? null
                      : (v) async {
                          await bind.mainSetOption(
                              key: kOptionAllowAutoRecordIncoming,
                              value: bool2option(
                                  kOptionAllowAutoRecordIncoming, v));
                          final newValue = option2bool(
                              kOptionAllowAutoRecordIncoming,
                              await bind.mainGetOption(
                                  key: kOptionAllowAutoRecordIncoming));
                          setState(() {
                            _autoRecordIncomingSession = newValue;
                          });
                        },
                ),
              if (!incomingOnly)
                SettingsTile.switchTile(
                  title:
                      Text(translate('Automatically record outgoing sessions')),
                  initialValue: _autoRecordOutgoingSession,
                  onToggle: isOptionFixed(kOptionAllowAutoRecordOutgoing)
                      ? null
                      : (v) async {
                          await bind.mainSetLocalOption(
                              key: kOptionAllowAutoRecordOutgoing,
                              value: bool2option(
                                  kOptionAllowAutoRecordOutgoing, v));
                          final newValue = option2bool(
                              kOptionAllowAutoRecordOutgoing,
                              bind.mainGetLocalOption(
                                  key: kOptionAllowAutoRecordOutgoing));
                          setState(() {
                            _autoRecordOutgoingSession = newValue;
                          });
                        },
                ),
              SettingsTile(
                title: Text(translate("Directory")),
                description: Text(bind.mainVideoSaveDirectory(root: false)),
              ),
            ],
          ),
        if (isAndroid &&
            !disabledSettings &&
            !outgoingOnly &&
            !hideSecuritySettings)
          SettingsSection(title: Text('2FA'), tiles: tfaTiles),
        if (isAndroid &&
            !disabledSettings &&
            !outgoingOnly &&
            !hideSecuritySettings)
          SettingsSection(
            title: Text(translate("Share screen")),
            tiles: shareScreenTiles,
          ),
        if (!bind.isIncomingOnly()) defaultDisplaySection(),
        if (isAndroid &&
            !disabledSettings &&
            !outgoingOnly &&
            !hideSecuritySettings)
          SettingsSection(
            title: Text(translate("Enhancements")),
            tiles: enhancementsTiles,
          ),
        SettingsSection(
          title: Text(translate("About")),
          tiles: [
            SettingsTile(
                title: Text(translate("Version: ") + version),
                leading: Icon(Icons.info),
                // Tap 7 times to enable developer mode (show ID/Relay Server)
                onPressed: (context) {
                  _versionTapCount++;
                  if (_versionTapCount >= 7) {
                    setState(() {
                      _developerModeEnabled = true;
                      _versionTapCount = 0;
                    });
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('Developer mode enabled! ID/Relay Server is now visible.'),
                        backgroundColor: Colors.green,
                        duration: Duration(seconds: 2),
                      ),
                    );
                  } else if (_versionTapCount >= 4) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text('${7 - _versionTapCount} more taps to enable developer mode'),
                        duration: Duration(milliseconds: 500),
                      ),
                    );
                  }
                }),
            SettingsTile(
                title: Text(translate("Build Date")),
                value: Padding(
                  padding: EdgeInsets.symmetric(vertical: 8),
                  child: Text(_buildDate),
                ),
                leading: Icon(Icons.query_builder)),
            if (isAndroid)
              SettingsTile(
                  onPressed: (context) => onCopyFingerprint(_fingerprint),
                  title: Text(translate("Fingerprint")),
                  value: Padding(
                    padding: EdgeInsets.symmetric(vertical: 8),
                    child: Text(_fingerprint),
                  ),
                  leading: Icon(Icons.fingerprint))
          ],
        ),
      ],
    );
    return settings;
  }

  Future<bool> canStartOnBoot() async {
    // start on boot depends on ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS and SYSTEM_ALERT_WINDOW
    if (_hasIgnoreBattery && !_ignoreBatteryOpt) {
      return false;
    }
    if (!await AndroidPermissionManager.check(kSystemAlertWindow)) {
      return false;
    }
    return true;
  }

  defaultDisplaySection() {
    return SettingsSection(
      title: Text(translate("Display Settings")),
      tiles: [
        SettingsTile(
            title: Text(translate('Display Settings')),
            leading: Icon(Icons.desktop_windows_outlined),
            trailing: Icon(Icons.arrow_forward_ios),
            onPressed: (context) {
              Navigator.push(context, MaterialPageRoute(builder: (context) {
                return _DisplayPage();
              }));
            })
      ],
    );
  }
}

void showLanguageSettings(OverlayDialogManager dialogManager) async {
  try {
    final langs = json.decode(await bind.mainGetLangs()) as List<dynamic>;
    var lang = bind.mainGetLocalOption(key: kCommConfKeyLang);
    dialogManager.show((setState, close, context) {
      setLang(v) async {
        if (lang != v) {
          setState(() {
            lang = v;
          });
          await bind.mainSetLocalOption(key: kCommConfKeyLang, value: v);
          HomePage.homeKey.currentState?.refreshPages();
          Future.delayed(Duration(milliseconds: 200), close);
        }
      }

      final isOptFixed = isOptionFixed(kCommConfKeyLang);
      return CustomAlertDialog(
        content: Column(
          children: [
                getRadio(Text(translate('Default')), defaultOptionLang, lang,
                    isOptFixed ? null : setLang),
                Divider(color: MyTheme.border),
              ] +
              langs.map((e) {
                final key = e[0] as String;
                final name = e[1] as String;
                return getRadio(Text(translate(name)), key, lang,
                    isOptFixed ? null : setLang);
              }).toList(),
        ),
      );
    }, backDismiss: true, clickMaskDismiss: true);
  } catch (e) {
    //
  }
}

void showThemeSettings(OverlayDialogManager dialogManager) async {
  var themeMode = MyTheme.getThemeModePreference();

  dialogManager.show((setState, close, context) {
    setTheme(v) {
      if (themeMode != v) {
        setState(() {
          themeMode = v;
        });
        MyTheme.changeDarkMode(themeMode);
        Future.delayed(Duration(milliseconds: 200), close);
      }
    }

    final isOptFixed = isOptionFixed(kCommConfKeyTheme);
    return CustomAlertDialog(
      content: Column(children: [
        getRadio(Text(translate('Light')), ThemeMode.light, themeMode,
            isOptFixed ? null : setTheme),
        getRadio(Text(translate('Dark')), ThemeMode.dark, themeMode,
            isOptFixed ? null : setTheme),
        getRadio(Text(translate('Follow System')), ThemeMode.system, themeMode,
            isOptFixed ? null : setTheme)
      ]),
    );
  }, backDismiss: true, clickMaskDismiss: true);
}

void showAbout(OverlayDialogManager dialogManager) {
  dialogManager.show((setState, close, context) {
    return CustomAlertDialog(
      title: Text(translate('About AFK Zone')),
      content: Wrap(direction: Axis.vertical, spacing: 12, children: [
        Text('Version: $version'),
      ]),
      actions: [],
    );
  }, clickMaskDismiss: true, backDismiss: true);
}

class ScanButton extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return IconButton(
      icon: Icon(Icons.qr_code_scanner),
      onPressed: () {
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (BuildContext context) => ScanPage(),
          ),
        );
      },
    );
  }
}

class _DisplayPage extends StatefulWidget {
  const _DisplayPage();

  @override
  State<_DisplayPage> createState() => __DisplayPageState();
}

class __DisplayPageState extends State<_DisplayPage> {
  @override
  Widget build(BuildContext context) {
    final Map codecsJson = jsonDecode(bind.mainSupportedHwdecodings());
    final h264 = codecsJson['h264'] ?? false;
    final h265 = codecsJson['h265'] ?? false;
    var codecList = [
      _RadioEntry('Auto', 'auto'),
      _RadioEntry('VP8', 'vp8'),
      _RadioEntry('VP9', 'vp9'),
      _RadioEntry('AV1', 'av1'),
      if (h264) _RadioEntry('H264', 'h264'),
      if (h265) _RadioEntry('H265', 'h265')
    ];
    RxBool showCustomImageQuality = false.obs;
    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
            onPressed: () => Navigator.pop(context),
            icon: Icon(Icons.arrow_back_ios)),
        title: Text(translate('Display Settings')),
        centerTitle: true,
      ),
      body: SettingsList(sections: [
        SettingsSection(
          tiles: [
            _getPopupDialogRadioEntry(
              title: 'Default View Style',
              list: [
                _RadioEntry('Scale original', kRemoteViewStyleOriginal),
                _RadioEntry('Scale adaptive', kRemoteViewStyleAdaptive)
              ],
              getter: () =>
                  bind.mainGetUserDefaultOption(key: kOptionViewStyle),
              asyncSetter: isOptionFixed(kOptionViewStyle)
                  ? null
                  : (value) async {
                      await bind.mainSetUserDefaultOption(
                          key: kOptionViewStyle, value: value);
                    },
            ),
            _getPopupDialogRadioEntry(
              title: 'Default Image Quality',
              list: [
                _RadioEntry('Good image quality', kRemoteImageQualityBest),
                _RadioEntry('Balanced', kRemoteImageQualityBalanced),
                _RadioEntry('Optimize reaction time', kRemoteImageQualityLow),
                _RadioEntry('Custom', kRemoteImageQualityCustom),
              ],
              getter: () {
                final v =
                    bind.mainGetUserDefaultOption(key: kOptionImageQuality);
                showCustomImageQuality.value = v == kRemoteImageQualityCustom;
                return v;
              },
              asyncSetter: isOptionFixed(kOptionImageQuality)
                  ? null
                  : (value) async {
                      await bind.mainSetUserDefaultOption(
                          key: kOptionImageQuality, value: value);
                      showCustomImageQuality.value =
                          value == kRemoteImageQualityCustom;
                    },
              tail: customImageQualitySetting(),
              showTail: showCustomImageQuality,
              notCloseValue: kRemoteImageQualityCustom,
            ),
            _getPopupDialogRadioEntry(
              title: 'Default Codec',
              list: codecList,
              getter: () =>
                  bind.mainGetUserDefaultOption(key: kOptionCodecPreference),
              asyncSetter: isOptionFixed(kOptionCodecPreference)
                  ? null
                  : (value) async {
                      await bind.mainSetUserDefaultOption(
                          key: kOptionCodecPreference, value: value);
                    },
            ),
          ],
        ),
        SettingsSection(
          title: Text(translate('Other Default Options')),
          tiles:
              otherDefaultSettings().map((e) => otherRow(e.$1, e.$2)).toList(),
        ),
      ]),
    );
  }

  SettingsTile otherRow(String label, String key) {
    final value = bind.mainGetUserDefaultOption(key: key) == 'Y';
    final isOptFixed = isOptionFixed(key);
    return SettingsTile.switchTile(
      initialValue: value,
      title: Text(translate(label)),
      onToggle: isOptFixed
          ? null
          : (b) async {
              await bind.mainSetUserDefaultOption(
                  key: key, value: b ? 'Y' : defaultOptionNo);
              setState(() {});
            },
    );
  }
}

class _ManageTrustedDevices extends StatefulWidget {
  const _ManageTrustedDevices();

  @override
  State<_ManageTrustedDevices> createState() => __ManageTrustedDevicesState();
}

class __ManageTrustedDevicesState extends State<_ManageTrustedDevices> {
  RxList<TrustedDevice> trustedDevices = RxList.empty(growable: true);
  RxList<Uint8List> selectedDevices = RxList.empty();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(translate('Manage trusted devices')),
        centerTitle: true,
        actions: [
          Obx(() => IconButton(
              icon: Icon(Icons.delete, color: Colors.white),
              onPressed: selectedDevices.isEmpty
                  ? null
                  : () {
                      confrimDeleteTrustedDevicesDialog(
                          trustedDevices, selectedDevices);
                    }))
        ],
      ),
      body: FutureBuilder(
          future: TrustedDevice.get(),
          builder: (context, snapshot) {
            if (snapshot.connectionState == ConnectionState.waiting) {
              return Center(child: CircularProgressIndicator());
            }
            if (snapshot.hasError) {
              return Center(child: Text('Error: ${snapshot.error}'));
            }
            final devices = snapshot.data as List<TrustedDevice>;
            trustedDevices = devices.obs;
            return trustedDevicesTable(trustedDevices, selectedDevices);
          }),
    );
  }
}

class _RadioEntry {
  final String label;
  final String value;
  _RadioEntry(this.label, this.value);
}

typedef _RadioEntryGetter = String Function();
typedef _RadioEntrySetter = Future<void> Function(String);

SettingsTile _getPopupDialogRadioEntry({
  required String title,
  required List<_RadioEntry> list,
  required _RadioEntryGetter getter,
  required _RadioEntrySetter? asyncSetter,
  Widget? tail,
  RxBool? showTail,
  String? notCloseValue,
}) {
  RxString groupValue = ''.obs;
  RxString valueText = ''.obs;

  init() {
    groupValue.value = getter();
    final e = list.firstWhereOrNull((e) => e.value == groupValue.value);
    if (e != null) {
      valueText.value = e.label;
    }
  }

  init();

  void showDialog() async {
    gFFI.dialogManager.show((setState, close, context) {
      final onChanged = asyncSetter == null
          ? null
          : (String? value) async {
              if (value == null) return;
              await asyncSetter(value);
              init();
              if (value != notCloseValue) {
                close();
              }
            };

      return CustomAlertDialog(
          content: Obx(
        () => Column(children: [
          ...list
              .map((e) => getRadio(Text(translate(e.label)), e.value,
                  groupValue.value, onChanged))
              .toList(),
          Offstage(
            offstage:
                !(tail != null && showTail != null && showTail.value == true),
            child: tail,
          ),
        ]),
      ));
    }, backDismiss: true, clickMaskDismiss: true);
  }

  return SettingsTile(
    title: Text(translate(title)),
    onPressed: asyncSetter == null ? null : (context) => showDialog(),
    value: Padding(
      padding: EdgeInsets.symmetric(vertical: 8),
      child: Obx(() => Text(translate(valueText.value))),
    ),
  );
}

// Region Switch Dialog Content - fetches from GET /public/regions
class _RegionSwitchDialogContent extends StatefulWidget {
  final Function(Map<String, dynamic>) onApply;
  
  const _RegionSwitchDialogContent({Key? key, required this.onApply}) : super(key: key);
  
  @override
  _RegionSwitchDialogContentState createState() => _RegionSwitchDialogContentState();
}

class _RegionSwitchDialogContentState extends State<_RegionSwitchDialogContent> {
  List<Map<String, dynamic>> _regions = [];
  bool _isLoading = true;
  String? _error;
  
  @override
  void initState() {
    super.initState();
    _loadRegions();
  }
  
  Future<void> _loadRegions() async {
    try {
      final response = await http.get(
        Uri.parse('https://api.afkzone.cloud/public/regions'),
        headers: {'Cache-Control': 'no-cache'},
      ).timeout(Duration(seconds: 10));
      
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        final List<dynamic> regionsJson = data['regions'] ?? [];
        setState(() {
          _regions = regionsJson.map((r) => Map<String, dynamic>.from(r)).toList();
          _isLoading = false;
        });
      } else {
        setState(() {
          _error = 'Không thể tải danh sách vùng';
          _isLoading = false;
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Lỗi kết nối: $e';
        _isLoading = false;
      });
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Row(
        children: [
          Icon(Icons.public, color: Colors.blue),
          SizedBox(width: 8),
          Text('Chọn vùng máy chủ'),
        ],
      ),
      content: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Warning message
          Container(
            padding: EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: Colors.orange.shade50,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: Colors.orange.shade200),
            ),
            child: Row(
              children: [
                Icon(Icons.warning_amber, color: Colors.orange, size: 20),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    '2 máy phải cùng server để kết nối được với nhau.',
                    style: TextStyle(fontSize: 13, color: Colors.orange.shade900),
                  ),
                ),
              ],
            ),
          ),
          SizedBox(height: 16),
          Text('Chọn vùng:', style: TextStyle(fontWeight: FontWeight.w500)),
          SizedBox(height: 8),
          // Region list
          if (_isLoading)
            Center(child: CircularProgressIndicator())
          else if (_error != null)
            Text(_error!, style: TextStyle(color: Colors.red))
          else
            ..._regions.map((region) => ListTile(
              // F14 fix: Use display_name, fallback to hostname (not 'Unknown')
              title: Text(region['display_name'] ?? region['name'] ?? region['hostname'] ?? 'Ho Chi Minh (Default)'),
              subtitle: Text(region['id_server'] ?? region['hostname'] ?? ''),
              leading: Icon(
                Icons.flag,
                color: region['is_default'] == true ? Colors.red : Colors.blue,
              ),
              trailing: region['is_default'] == true 
                ? Container(
                    padding: EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.green.shade100,
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text('Mặc định', style: TextStyle(fontSize: 10, color: Colors.green)),
                  )
                : null,
              onTap: () {
                Navigator.pop(context);
                widget.onApply(region);
              },
              dense: true,
            )).toList(),
        ],
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: Text('Đóng'),
        ),
      ],
    );
  }
}

// Device List Dialog - shows activated devices with kick option
class _DeviceListDialogContent extends StatefulWidget {
  final String licenseKey;
  const _DeviceListDialogContent({Key? key, required this.licenseKey}) : super(key: key);
  @override
  _DeviceListDialogContentState createState() => _DeviceListDialogContentState();
}

class _DeviceListDialogContentState extends State<_DeviceListDialogContent> {
  List<Map<String, dynamic>> _devices = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadDevices();
  }

  Future<void> _loadDevices() async {
    setState(() => _isLoading = true);
    try {
      // Use JWT-authenticated /user/devices endpoint
      final response = await AuthService.authGet('/user/devices');
      if (response.statusCode == 200) {
        final data = json.decode(utf8.decode(response.bodyBytes));
        setState(() {
          _devices = (data['devices'] ?? []).map<Map<String, dynamic>>((d) => Map<String, dynamic>.from(d)).toList();
          _isLoading = false;
        });
      } else if (response.statusCode == 401) {
        setState(() { _error = 'Vui lòng đăng nhập lại'; _isLoading = false; });
      } else {
        setState(() { _error = 'Không thể tải danh sách'; _isLoading = false; });
      }
    } catch (e) {
      setState(() { _error = 'Lỗi kết nối: $e'; _isLoading = false; });
    }
  }

  Future<void> _kickDevice(String deviceId) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Xác nhận'),
        content: Text('Gỡ thiết bị này khỏi license?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: Text('Hủy')),
          ElevatedButton(onPressed: () => Navigator.pop(context, true), style: ElevatedButton.styleFrom(backgroundColor: Colors.red), child: Text('Gỡ')),
        ],
      ),
    );
    if (confirm != true) return;
    try {
      // Use JWT-authenticated DELETE /user/devices/{id}/clear endpoint
      final response = await AuthService.authDelete('/user/devices/$deviceId/clear');
      if (response.statusCode == 200) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('✅ Đã gỡ thiết bị'), backgroundColor: Colors.green));
        _loadDevices(); // Refresh list after kick
      } else if (response.statusCode == 401) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('❌ Phiên đăng nhập hết hạn'), backgroundColor: Colors.red));
      } else {
        final data = json.decode(response.body);
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('❌ ${data['detail'] ?? 'Lỗi gỡ thiết bị'}'), backgroundColor: Colors.red));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('❌ Lỗi kết nối: $e'), backgroundColor: Colors.red));
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Row(children: [Icon(Icons.list_alt, color: Colors.green), SizedBox(width: 8), Text('Thiết bị đã kích hoạt')]),
      content: Container(
        width: double.maxFinite,
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            if (_isLoading) Padding(padding: EdgeInsets.all(20), child: CircularProgressIndicator())
            else if (_error != null) Text(_error!, style: TextStyle(color: Colors.red))
            else if (_devices.isEmpty) Column(children: [Icon(Icons.devices_other, size: 48, color: Colors.grey), SizedBox(height: 12), Text('Chưa có thiết bị')])
            else ..._devices.map((d) => Card(
              child: ListTile(
                title: Text(d['alias'] ?? 'Thiết bị'),
                subtitle: Text('ID: ${(d['device_id'] ?? '').toString().length > 12 ? (d['device_id'] ?? '').toString().substring(0, 12) + '...' : d['device_id'] ?? ''}', style: TextStyle(fontSize: 11, fontFamily: 'monospace')),
                leading: Icon(Icons.phone_android, color: Colors.blue),
                trailing: IconButton(icon: Icon(Icons.delete_outline, color: Colors.red), onPressed: () => _kickDevice(d['device_id'] ?? ''), tooltip: 'Gỡ'),
                dense: true,
              ),
            )).toList(),
          ],
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: Text('Đóng')),
        ElevatedButton.icon(onPressed: _loadDevices, icon: Icon(Icons.refresh, size: 16), label: Text('Làm mới')),
      ],
    );
  }
}
