from pymongo import MongoClient

def fix_data():
    client = MongoClient('mongodb://localhost:27017')
    db = client.easy_book
    
    # 删除所有预约数据，重新开始
    result = db.appointments.delete_many({})
    print(f'删除了 {result.deleted_count} 条预约记录')
    
    # 删除所有考勤数据
    result = db.attendances.delete_many({})
    print(f'删除了 {result.deleted_count} 条考勤记录')
    
    client.close()
    print('数据清理完成')

if __name__ == "__main__":
    fix_data()