import 'package:flutter/material.dart';

class BigButton extends StatelessWidget {
  const BigButton({super.key, required this.label, required this.icon, required this.onTap, this.subtitle});
  final String label;
  final String? subtitle;
  final IconData icon;
  final VoidCallback onTap;
  @override
  Widget build(BuildContext context) => Semantics(
        button: true,
        label: label,
        child: Card(
          child: InkWell(
            onTap: onTap,
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Row(children: [
                Icon(icon, size: 40),
                const SizedBox(width: 16),
                Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(label, style: Theme.of(context).textTheme.titleLarge),
                  if (subtitle != null) Text(subtitle!),
                ])),
              ]),
            ),
          ),
        ),
      );
}
