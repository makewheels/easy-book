import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def cleanup_old_collection():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.easy_book

    print("=== Checking old collection ===")
    count = await db.student_appointments.count_documents({})
    print(f"student_appointments collection has {count} records")

    if count > 0:
        # Check for duplicates before deleting
        print("\nChecking for duplicates...")
        async for old_doc in db.student_appointments.find():
            duplicate = await db.appointments.find_one({
                "student_id": old_doc.get("student_id"),
                "course_id": old_doc.get("course_id")
            })
            if duplicate:
                print(f"Found duplicate: student_id={old_doc.get('student_id')}, course_id={old_doc.get('course_id')}")

        print("\n=== Deleting old collection ===")
        await db.student_appointments.drop()
        print("Successfully deleted student_appointments collection")

    # Verify deletion
    collections = await db.list_collection_names()
    print(f"\nCurrent collections: {collections}")

    if "student_appointments" not in collections:
        print("Confirmed: student_appointments collection has been deleted")
    else:
        print("Error: student_appointments collection still exists")

    client.close()

if __name__ == "__main__":
    asyncio.run(cleanup_old_collection())