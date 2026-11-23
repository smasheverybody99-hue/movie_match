import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:movie_match/main.dart';

void main() {
  testWidgets('the empty app shows its name', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: MovieMatchApp()));
    expect(find.text('Movie Match'), findsOneWidget);
  });
}
