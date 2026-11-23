import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'theme/tokens.dart';

void main() => runApp(const ProviderScope(child: MovieMatchApp()));

class MovieMatchApp extends StatelessWidget {
  const MovieMatchApp({super.key});

  @override
  Widget build(BuildContext context) => MaterialApp(
        title: 'Movie Match',
        theme: buildTheme(),
        home: const Scaffold(
          body: Center(child: Text('Movie Match')),
        ),
      );
}
