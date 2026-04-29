import 'dart:ui';
import 'package:flutter/material.dart';
import 'colors.dart';
import 'typography.dart';

class GlassCard extends StatelessWidget {
  const GlassCard({
    super.key,
    required this.child,
    this.padding = const EdgeInsets.all(20),
    this.darkMode = false,
    this.borderRadius = 20,
    this.margin,
  });

  final Widget child;
  final EdgeInsetsGeometry padding;
  final bool darkMode;
  final double borderRadius;
  final EdgeInsetsGeometry? margin;

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: margin,
      decoration: BoxDecoration(
        color: darkMode ? AppColors.surfaceGlassDark : AppColors.surfaceGlass,
        borderRadius: BorderRadius.circular(borderRadius),
        border: Border.all(
          color: Colors.white.withOpacity(darkMode ? 0.12 : 0.5),
          width: 1.0,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.06),
            blurRadius: 20,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(borderRadius),
        child: BackdropFilter(
          filter: ImageFilter.blur(sigmaX: 12, sigmaY: 12),
          child: Padding(
            padding: padding,
            child: child,
          ),
        ),
      ),
    );
  }
}

class GlassButton extends StatelessWidget {
  const GlassButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
    this.variant = GlassButtonVariant.primary,
    this.width,
    this.height = 52,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final GlassButtonVariant variant;
  final double? width;
  final double height;

  @override
  Widget build(BuildContext context) {
    if (variant == GlassButtonVariant.primary) {
      return _PrimaryButton(
        label: label,
        onPressed: onPressed,
        icon: icon,
        width: width,
        height: height,
      );
    }
    return _OutlineButton(
      label: label,
      onPressed: onPressed,
      icon: icon,
      width: width,
      height: height,
    );
  }
}

enum GlassButtonVariant { primary, outline }

class _PrimaryButton extends StatelessWidget {
  const _PrimaryButton({
    required this.label,
    required this.onPressed,
    this.icon,
    this.width,
    required this.height,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final double? width;
  final double height;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onPressed,
      child: Container(
        width: width,
        height: height,
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [AppColors.secondary, Color(0xFF0E7A88)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(14),
          boxShadow: [
            BoxShadow(
              color: AppColors.secondary.withOpacity(0.35),
              blurRadius: 16,
              offset: const Offset(0, 6),
            ),
          ],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: width == null ? MainAxisSize.min : MainAxisSize.max,
          children: [
            if (icon != null) ...[
              Icon(icon, color: Colors.white, size: 20),
              const SizedBox(width: 8),
            ],
            Padding(
              padding: EdgeInsets.symmetric(horizontal: icon == null ? 24 : 0),
              child: Text(
                label,
                style: AppTypography.labelLarge.copyWith(
                  color: Colors.white,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _OutlineButton extends StatelessWidget {
  const _OutlineButton({
    required this.label,
    required this.onPressed,
    this.icon,
    this.width,
    required this.height,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;
  final double? width;
  final double height;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onPressed,
      child: Container(
        width: width,
        height: height,
        decoration: BoxDecoration(
          color: Colors.transparent,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: AppColors.secondary.withOpacity(0.6),
            width: 1.5,
          ),
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          mainAxisSize: width == null ? MainAxisSize.min : MainAxisSize.max,
          children: [
            if (icon != null) ...[
              Icon(icon, color: AppColors.secondary, size: 20),
              const SizedBox(width: 8),
            ],
            Padding(
              padding: EdgeInsets.symmetric(horizontal: icon == null ? 24 : 0),
              child: Text(
                label,
                style: AppTypography.labelLarge.copyWith(
                  color: AppColors.secondary,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class GlassAppBar extends StatelessWidget implements PreferredSizeWidget {
  const GlassAppBar({
    super.key,
    required this.title,
    this.leading,
    this.actions,
    this.darkMode = false,
    this.subtitle,
  });

  final String title;
  final Widget? leading;
  final List<Widget>? actions;
  final bool darkMode;
  final String? subtitle;

  @override
  Size get preferredSize => const Size.fromHeight(72);

  @override
  Widget build(BuildContext context) {
    return ClipRect(
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 20, sigmaY: 20),
        child: Container(
          height: preferredSize.height + MediaQuery.of(context).padding.top,
          padding: EdgeInsets.only(
            top: MediaQuery.of(context).padding.top,
            left: 16,
            right: 16,
          ),
          decoration: BoxDecoration(
            color: darkMode
                ? AppColors.surfaceGlassDark
                : Colors.white.withOpacity(0.85),
            border: Border(
              bottom: BorderSide(
                color: Colors.white.withOpacity(darkMode ? 0.1 : 0.4),
                width: 1,
              ),
            ),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              if (leading != null) ...[
                leading!,
                const SizedBox(width: 12),
              ],
              Expanded(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: AppTypography.headlineMedium.copyWith(
                        color: darkMode ? Colors.white : AppColors.textPrimary,
                      ),
                    ),
                    if (subtitle != null)
                      Text(
                        subtitle!,
                        style: AppTypography.bodySmall.copyWith(
                          color: darkMode
                              ? Colors.white60
                              : AppColors.textSecondary,
                        ),
                      ),
                  ],
                ),
              ),
              if (actions != null) ...actions!,
            ],
          ),
        ),
      ),
    );
  }
}

class MeshGradientBackground extends StatelessWidget {
  const MeshGradientBackground({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [
                AppColors.gradientStart,
                AppColors.gradientMid,
                Color(0xFF0F3557),
              ],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
        ),
        Positioned(
          top: -80,
          right: -60,
          child: Container(
            width: 280,
            height: 280,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppColors.secondary.withOpacity(0.15),
            ),
          ),
        ),
        Positioned(
          bottom: -100,
          left: -80,
          child: Container(
            width: 320,
            height: 320,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppColors.primary.withOpacity(0.5),
            ),
          ),
        ),
        child,
      ],
    );
  }
}
