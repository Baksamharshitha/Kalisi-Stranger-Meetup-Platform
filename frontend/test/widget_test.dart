import 'package:flutter_test/flutter_test.dart';
import 'package:kalisi_frontend/main.dart';

void main() {
  testWidgets('KalisiApp basic smoke test', (WidgetTester tester) async {
    await tester.pumpWidget(const KalisiApp());
    expect(find.text('Kalisi'), findsWidgets);
  });
}
