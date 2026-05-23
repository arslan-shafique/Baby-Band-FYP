import 'dart:io';
import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:image_picker/image_picker.dart'; 
import 'package:firebase_storage/firebase_storage.dart'; 
import 'dash.dart';
import 'services/fcm_service.dart';
import 'globals.dart';

class SignupPage extends StatefulWidget {
  const SignupPage({super.key});

  @override
  State<SignupPage> createState() => _SignupPageState();
}

class _SignupPageState extends State<SignupPage> {
  final TextEditingController nameController = TextEditingController();
  final TextEditingController emailController = TextEditingController();
  final TextEditingController phoneController = TextEditingController();
  final TextEditingController babyNameController = TextEditingController();
  final TextEditingController deviceIdController = TextEditingController();
  final TextEditingController passwordController = TextEditingController();
  final TextEditingController confirmPasswordController = TextEditingController();
  final _formKey = GlobalKey<FormState>();

  bool isLoading = false;
  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;
  
  File? _profileImage;

  Future<void> _pickImage() async {
    
    final ImagePicker picker = ImagePicker();
    final XFile? image = await picker.pickImage(source: ImageSource.gallery);
    
    if (image != null) {
      setState(() {
        _profileImage = File(image.path);
      });
    }
    
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Please run: flutter pub add image_picker firebase_storage first!')),
    );
  }

  Future<void> registerUser() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => isLoading = true);

    try {
      // 1. Create user in Firebase Auth
      final credential = await FirebaseAuth.instance.createUserWithEmailAndPassword(
        email: emailController.text.trim(),
        password: passwordController.text,
      );

      final user = credential.user;
      if (user != null) {
        String? profileImageUrl;

        // 2. Upload Profile Image to Firebase Storage (Uncomment after installing packages)
        
        if (_profileImage != null) {
          final storageRef = FirebaseStorage.instance
              .ref()
              .child('user_profiles')
              .child('${user.uid}.jpg');
          
          await storageRef.putFile(_profileImage!);
          profileImageUrl = await storageRef.getDownloadURL();
        }
        

        // 3. Store extended user data in Firestore
        await FirebaseFirestore.instance.collection('users').doc(user.uid).set({
          'name': nameController.text.trim(),
          'email': emailController.text.trim(),
          'phone': phoneController.text.trim(),
          'baby_name': babyNameController.text.trim(),
          'role': 'parent',
          'profile_image': profileImageUrl ?? '',
          'created_at': FieldValue.serverTimestamp(),
        });

        // 3.5 Create Baby Profile Document
        final deviceId = deviceIdController.text.trim();
        await FirebaseFirestore.instance.collection('baby_profiles').doc(deviceId).set({
          'user_id': user.uid,
          'name': babyNameController.text.trim(),
          'device_id': deviceId,
          'created_at': FieldValue.serverTimestamp(),
        });
        
        // Update the global state so the dashboard loads immediately
        await saveDeviceId(deviceId);

        // 4. Initialize FCM
        await FcmService.initialize();

        if (mounted) {
          Navigator.pushAndRemoveUntil(
            context,
            MaterialPageRoute(builder: (context) => const DashboardPage()),
            (route) => false,
          );
        }
      }
    } on FirebaseAuthException catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text(e.message ?? 'Registration failed')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('An error occurred: $e')),
        );
      }
    } finally {
      if (mounted) {
        setState(() => isLoading = false);
      }
    }
  }

  @override
  void dispose() {
    nameController.dispose();
    emailController.dispose();
    phoneController.dispose();
    babyNameController.dispose();
    deviceIdController.dispose();
    passwordController.dispose();
    confirmPasswordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final colorScheme = theme.colorScheme;

    return Scaffold(
      appBar: AppBar(
        title: Text(
          'SIGN UP',
          style: theme.textTheme.headlineMedium,
        ),
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 20),
            child: Form(
              key: _formKey,
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [

                  GestureDetector(
                    onTap: _pickImage,
                    child: Stack(
                      alignment: Alignment.bottomRight,
                      children: [
                        Container(
                          width: 120,
                          height: 120,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: colorScheme.primary.withValues(alpha: 0.15),
                            border: Border.all(
                              color: colorScheme.primary,
                              width: 2,
                            ),
                            image: _profileImage != null
                                ? DecorationImage(
                                    image: FileImage(_profileImage!),
                                    fit: BoxFit.cover,
                                  )
                                : null,
                          ),
                          child: _profileImage == null
                              ? Icon(
                                  Icons.person_rounded,
                                  size: 60,
                                  color: colorScheme.primary,
                                )
                              : null,
                        ),
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: colorScheme.primary,
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(
                            Icons.camera_alt_rounded,
                            color: Colors.white,
                            size: 20,
                          ),
                        ),
                      ],
                    ),
                  ),

                  const SizedBox(height: 24),
                  Text(
                    'Parent Details',
                    style: theme.textTheme.titleLarge?.copyWith(
                      color: colorScheme.primary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Name field
                  TextFormField(
                    controller: nameController,
                    keyboardType: TextInputType.name,
                    validator: (value) => value!.isEmpty ? 'Name is required' : null,
                    decoration: const InputDecoration(
                      labelText: 'Full Name',
                      prefixIcon: Icon(Icons.person_outline),
                    ),
                  ),

                  const SizedBox(height: 16),

                  // Email field
                  TextFormField(
                    controller: emailController,
                    keyboardType: TextInputType.emailAddress,
                    validator: (value) {
                      if (value == null || value.isEmpty) return 'Email is required';
                      if (!value.contains('@')) return 'Enter a valid email';
                      return null;
                    },
                    decoration: const InputDecoration(
                      labelText: 'Email',
                      prefixIcon: Icon(Icons.email_outlined),
                    ),
                  ),

                  const SizedBox(height: 16),

                  // Phone field
                  TextFormField(
                    controller: phoneController,
                    keyboardType: TextInputType.phone,
                    validator: (value) => value!.isEmpty ? 'Phone number is required' : null,
                    decoration: const InputDecoration(
                      labelText: 'Phone Number',
                      prefixIcon: Icon(Icons.phone_outlined),
                    ),
                  ),

                  const SizedBox(height: 24),
                  Text(
                    'Baby Details',
                    style: theme.textTheme.titleLarge?.copyWith(
                      color: colorScheme.primary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Baby Name field
                  TextFormField(
                    controller: babyNameController,
                    keyboardType: TextInputType.name,
                    validator: (value) => value!.isEmpty ? 'Baby\'s name is required' : null,
                    decoration: const InputDecoration(
                      labelText: 'Baby\'s Name',
                      prefixIcon: Icon(Icons.child_care_rounded),
                    ),
                  ),

                  const SizedBox(height: 16),

                  // Device ID field
                  TextFormField(
                    controller: deviceIdController,
                    keyboardType: TextInputType.text,
                    validator: (value) => value!.isEmpty ? 'Device ID is required' : null,
                    decoration: const InputDecoration(
                      labelText: 'Device ID (e.g. babyband_01)',
                      prefixIcon: Icon(Icons.watch_rounded),
                    ),
                  ),

                  const SizedBox(height: 24),
                  Text(
                    'Security',
                    style: theme.textTheme.titleLarge?.copyWith(
                      color: colorScheme.primary,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 16),

                  // Password field
                  TextFormField(
                    controller: passwordController,
                    obscureText: _obscurePassword,
                    validator: (value) {
                      if (value == null || value.isEmpty) return 'Password is required';
                      if (value.length < 6) return 'Password must be at least 6 characters';
                      return null;
                    },
                    decoration: InputDecoration(
                      labelText: 'Password',
                      prefixIcon: const Icon(Icons.lock_outlined),
                      suffixIcon: IconButton(
                        icon: Icon(_obscurePassword ? Icons.visibility_off_outlined : Icons.visibility_outlined),
                        onPressed: () => setState(() => _obscurePassword = !_obscurePassword),
                      ),
                    ),
                  ),

                  const SizedBox(height: 16),

                  // Confirm Password field
                  TextFormField(
                    controller: confirmPasswordController,
                    obscureText: _obscureConfirmPassword,
                    validator: (value) {
                      if (value == null || value.isEmpty) return 'Please confirm your password';
                      if (value != passwordController.text) return 'Passwords do not match!';
                      return null;
                    },
                    decoration: InputDecoration(
                      labelText: 'Confirm Password',
                      prefixIcon: const Icon(Icons.lock_reset_outlined),
                      suffixIcon: IconButton(
                        icon: Icon(_obscureConfirmPassword ? Icons.visibility_off_outlined : Icons.visibility_outlined),
                        onPressed: () => setState(() => _obscureConfirmPassword = !_obscureConfirmPassword),
                      ),
                    ),
                  ),

                  const SizedBox(height: 32),

                  // Sign up button
                  SizedBox(
                    width: double.infinity,
                    child: isLoading
                        ? Center(child: CircularProgressIndicator(color: colorScheme.primary))
                        : ElevatedButton(
                            onPressed: registerUser,
                            child: const Padding(
                              padding: EdgeInsets.symmetric(vertical: 12),
                              child: Text('CREATE ACCOUNT', style: TextStyle(fontSize: 16)),
                            ),
                          ),
                  ),

                  const SizedBox(height: 16),

                  // Back to Login
                  Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Text(
                        'Already have an account?',
                        style: theme.textTheme.bodyMedium?.copyWith(
                          color: colorScheme.onSurfaceVariant,
                        ),
                      ),
                      TextButton(
                        onPressed: () => Navigator.pop(context),
                        child: const Text('Log In'),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
