import 'package:flutter/material.dart';
import 'constants.dart';

class BottomButton extends StatelessWidget {
  final String title;
  final VoidCallback onTap;

  const BottomButton({super.key, required this.title, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        color: kbuttomcontainercolor,
        margin: const EdgeInsets.only(top: 9.0),
        width: double.infinity,
        height: kbuttomcontainerhight,
        child: Center(child: Text(title, style: klargeText)),
      ),
    );
  }
}
