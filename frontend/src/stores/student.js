import { defineStore } from 'pinia'
import { studentApi } from '@/api/student'

export const useStudentStore = defineStore('student', {
  state: () => ({
    students: [],
    currentStudent: null,
    loading: false,
    error: null
  }),
  
  getters: {
    totalStudents: (state) => state.students.length,
    activeStudents: (state) => state.students.filter(s => s.remaining_lessons > 0),
    getStudentById: (state) => (id) => state.students.find(s => s.id === id)
  },
  
  actions: {
    async fetchStudents() {
      this.loading = true
      this.error = null
      
      try {
        this.students = await studentApi.getAll()
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async createStudent(studentData) {
      this.loading = true
      
      try {
        const newStudent = await studentApi.create(studentData)
        this.students.push(newStudent)
        return newStudent
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async updateStudent(id, data) {
      this.loading = true
      
      try {
        const updatedStudent = await studentApi.update(id, data)
        const index = this.students.findIndex(s => s.id === id)
        if (index !== -1) {
          this.students[index] = updatedStudent
        }
        
        if (this.currentStudent?.id === id) {
          this.currentStudent = updatedStudent
        }
        
        return updatedStudent
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async deleteStudent(id) {
      this.loading = true
      
      try {
        await studentApi.delete(id)
        this.students = this.students.filter(s => s.id !== id)
        
        if (this.currentStudent?.id === id) {
          this.currentStudent = null
        }
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    
    async fetchStudentById(id) {
      this.loading = true
      
      try {
        this.currentStudent = await studentApi.getById(id)
        return this.currentStudent
      } catch (error) {
        this.error = error.message
        throw error
      } finally {
        this.loading = false
      }
    },
    
    setCurrentStudent(student) {
      this.currentStudent = student
    },
    
    clearError() {
      this.error = null
    }
  }
})