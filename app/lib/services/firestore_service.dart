import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_database/firebase_database.dart';

class FirestoreService {
  static final FirebaseFirestore _db = FirebaseFirestore.instance;
  static final FirebaseDatabase _rtdb = FirebaseDatabase.instance;

  static Stream<List<Map<String, dynamic>>> getCryEvents(String deviceId) {
    return _db
        .collection('cry_events')
        .where('baby_id', isEqualTo: deviceId) // backend uses baby_id for this
        .orderBy('timestamp', descending: true)
        .limit(20)
        .snapshots()
        .map((snapshot) => snapshot.docs.map((doc) => doc.data()).toList());
  }

  static Stream<List<Map<String, dynamic>>> getSleepSessions(String deviceId) {
    return _db
        .collection('sleep_sessions')
        .where('device_id', isEqualTo: deviceId)
        .orderBy('timestamp', descending: true)
        .limit(20)
        .snapshots()
        .map((snapshot) => snapshot.docs.map((doc) => doc.data()).toList());
  }

  static Stream<List<Map<String, dynamic>>> getEnvironmentLogs(String deviceId) {
    return _db
        .collection('environment_logs')
        .where('device_id', isEqualTo: deviceId)
        .orderBy('timestamp', descending: true)
        .limit(144)
        .snapshots()
        .map((snapshot) => snapshot.docs.map((doc) => doc.data()).toList());
  }

  static Stream<List<Map<String, dynamic>>> getSensorData(String deviceId) {
    return _db
        .collection('sensor_data')
        .where('device_id', isEqualTo: deviceId)
        .orderBy('timestamp', descending: true)
        .limit(144)
        .snapshots()
        .map((snapshot) => snapshot.docs.map((doc) => doc.data()).toList());
  }

  static Stream<Map<String, dynamic>?> getBabyProfile(String deviceId) {
    return _db
        .collection('baby_profiles')
        .where(FieldPath.documentId, isEqualTo: deviceId)
        .snapshots()
        .map((snapshot) {
          if (snapshot.docs.isNotEmpty) return snapshot.docs.first.data();
          return null;
        });
  }

  static Stream<Map<String, dynamic>?> getCryClassifications(String deviceId) {
    return _rtdb
        .ref('cry_classifications')
        .orderByChild('device_id')
        .equalTo(deviceId)
        .limitToLast(1)
        .onValue
        .map((event) {
          final data = event.snapshot.value;
          if (data != null && data is Map) {
            final key = data.keys.last;
            return Map<String, dynamic>.from(data[key]);
          }
          return null;
        });
  }

  static Stream<List<Map<String, dynamic>>> getNotifications(String userId) {
    return _db
        .collection('notifications')
        .where('user_id', isEqualTo: userId)
        .snapshots()
        .map((snapshot) {
          final list = snapshot.docs.map((doc) {
            final data = doc.data();
            data['id'] = doc.id;
            return data;
          }).toList();
          
          // Sort in-memory to completely bypass the Firestore index requirement
          list.sort((a, b) {
            final aTime = a['created_at'];
            final bTime = b['created_at'];
            if (aTime == null || bTime == null) return 0;
            if (aTime is Timestamp && bTime is Timestamp) {
              return bTime.compareTo(aTime); // Descending (latest first)
            }
            return 0;
          });
          return list;
        });
  }

  static Future<void> markNotificationAsRead(String notificationId) async {
    await _db.collection('notifications').doc(notificationId).update({'is_read': true});
  }

  static Future<void> clearAllNotifications(String userId) async {
    final batch = _db.batch();
    final snapshots = await _db.collection('notifications').where('user_id', isEqualTo: userId).get();
    for (final doc in snapshots.docs) {
      batch.delete(doc.reference);
    }
    await batch.commit();
  }
}
