import 'package:flutter/material.dart';

class ReusableCard extends StatelessWidget {
  const ReusableCard({
    super.key,
    required this.color,
    this.cardchild,
    required this.onPress,
  });

  final Color color;
  final Widget? cardchild; // nullable
  final VoidCallback? onPress; // VOID FUNCTION
  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onPress,
      child: Container(
        margin: const EdgeInsets.all(15.0),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(10),
          color: color, // ✅ use the provided color
        ),
        child: cardchild,
      ),
    );
  }
}
