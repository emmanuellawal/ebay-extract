// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter_test/flutter_test.dart';

import 'package:appraisal_app/main.dart';

void main() {
  testWidgets('App renders correctly', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(AppraisalApp());

    // Verify that the app has the correct title
    expect(find.text('Item Appraisal'), findsOneWidget);
    
    // Verify that the Take Photo button exists
    expect(find.text('Take Photo'), findsOneWidget);
  });
}
