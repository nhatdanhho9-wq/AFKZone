import 'package:flutter/material.dart';

import 'vnext_app.dart';

/// vNext standalone entrypoint (pure Dart).
/// Build with:
///   AFK_VNEXT_ONLY=1 flutter build apk -t lib/vnext/main_vnext.dart --debug ...
void main() {
  runApp(const MaterialApp(
    debugShowCheckedModeBanner: false,
    home: VNextApp(),
  ));
}

