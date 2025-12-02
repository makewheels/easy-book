// 创建应用数据库和用户
db = db.getSiblingDB('easy_book');

// 创建应用用户
db.createUser({
  user: 'easybook_user',
  pwd: 'easybook_pass',
  roles: [
    {
      role: 'readWrite',
      db: 'easy_book'
    }
  ]
});

// 创建集合和索引
db.createCollection('students');
db.students.createIndex({ "phone": 1 }, { unique: true });

db.createCollection('appointments');
db.appointments.createIndex({ "date": 1, "time": 1 });
db.appointments.createIndex({ "student_id": 1 });

db.createCollection('attendance');
db.attendance.createIndex({ "appointment_id": 1, "student_id": 1 }, { unique: true });

print('MongoDB initialization completed');