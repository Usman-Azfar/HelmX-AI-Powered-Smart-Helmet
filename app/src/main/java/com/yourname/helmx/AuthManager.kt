package com.yourname.helmx

import android.content.Context
import com.google.firebase.FirebaseNetworkException
import com.google.firebase.FirebaseTooManyRequestsException
import com.google.firebase.auth.FirebaseAuth
import com.google.firebase.auth.FirebaseAuthInvalidCredentialsException
import com.google.firebase.auth.FirebaseAuthInvalidUserException
import com.google.firebase.auth.FirebaseAuthUserCollisionException
import com.google.firebase.auth.FirebaseAuthWeakPasswordException
import com.google.firebase.auth.FirebaseUser
import com.google.firebase.auth.EmailAuthProvider
import com.google.firebase.firestore.FirebaseFirestore
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.tasks.await
import kotlinx.coroutines.withTimeoutOrNull

/**
 * Maps a Firebase Auth failure to a user-facing message based on the exception type
 * rather than its (unstable) message text.
 *
 * Note: with email enumeration protection enabled, Firebase reports both a wrong password and
 * an unknown email as invalid credentials, so they share one message.
 */
fun authErrorMessage(e: Throwable, action: String): String = when (e) {
    is FirebaseAuthWeakPasswordException -> "Password is too weak"
    is FirebaseAuthUserCollisionException -> "This email is already registered"
    is FirebaseAuthInvalidUserException -> "No account found with this email"
    is FirebaseAuthInvalidCredentialsException ->
        if (action == "Sign up") "Invalid email address" else "Incorrect email or password"
    is FirebaseNetworkException -> "Network error. Check your connection"
    is FirebaseTooManyRequestsException -> "Too many attempts. Please try again later"
    else -> "$action failed: ${e.message}"
}

class AuthManager {

    private val auth: FirebaseAuth = FirebaseAuth.getInstance()

    private val firestore: FirebaseFirestore = FirebaseFirestore.getInstance()

    fun getCurrentUser() : FirebaseUser? {
        return auth.currentUser
    }

    /**
     * Sign up new user with email and password
     *
     * @param email User's email address
     * @param password User's password (min 6 characters required by Firebase)
     * @param fullName User's full name
     * @param phoneNumber User's phone number
     * @return Result<String> - Success with UID or Failure with error message
     */
    suspend fun signUpWithEmail(
        email: String,
        password: String,
        fullName: String,
        phoneNumber: String
    ): Result<String> {
        return try {
            // Step 1: Create authentication account
            val authResult = auth.createUserWithEmailAndPassword(email, password).await()

            // Step 2: Get the newly created user's UID
            val uid = authResult.user?.uid ?: throw Exception("User creation failed")

            // Step 3: Create user document in Firestore
            val user = User(
                id = uid,
                fullname = fullName,
                email = email,
                phone = phoneNumber,
                createdAt = System.currentTimeMillis()
            )

            // Step 4: Save to Firestore "users" collection
            firestore.collection("users")
                .document(uid)
                .set(user)
                .await()

            // Step 5: Return success with UID
            Result.success(uid)

        } catch (e: Exception) {
            // If anything fails, return error message
            Result.failure(e)
        }
    }

    suspend fun signInWithEmail(
        email: String,
        password: String
    ): Result<String> {
        return try {
            // Authenticate user
            val authResult = auth.signInWithEmailAndPassword(email, password).await()

            // Get UID
            val uid = authResult.user?.uid ?: throw Exception("Log in failed")

            // Return success
            Result.success(uid)

        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Get user data from Firestore
     *
     * @param uid User's unique identifier
     * @return Result<User> - Success with User object or Failure
     */
    suspend fun getUserData(uid: String): Result<User> {
        return try {
            // Fetch user document from Firestore
            val document = firestore.collection("users")
                .document(uid)
                .get()
                .await()

            // Convert Firestore document to User object
            val user = document.toObject(User::class.java)
                ?: throw Exception("User data not found")

            Result.success(user)

        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Sign out current user
     */
    fun signOut() {
        auth.signOut()
    }

    /**
     * User-initiated logout: ends any ride in progress and disconnects the helmet so the next
     * user starts clean. Firestore attributes a write to whoever is signed in when it is made,
     * so we wait (briefly) for the ride service to queue the save before signing out.
     */
    suspend fun logout(context: Context) {
        if (RideSession.state.value.isRecording) {
            RideTrackingService.stop(context)
            withTimeoutOrNull(3000) { RideSession.state.first { !it.isRecording } }
        }
        // Give queued writes (e.g. the ride above) a moment to reach the server while still
        // signed in. If offline, they stay queued for this user until they sign in again.
        runCatching { withTimeoutOrNull(5000) { firestore.waitForPendingWrites().await() } }
        HelmetBleManager.getInstance(context).disconnect()
        SafetySettings.clearAccountData(context) // emergency contacts belong to this account
        RecentPlaces(context).clear()
        auth.signOut()
    }

    /**
     * Check if user is currently logged in
     */
    fun isUserLoggedIn(): Boolean {
        return auth.currentUser != null
    }

    suspend fun reauthenticate(password: String): Result<Boolean> {
        return try {
            val user = auth.currentUser ?: throw Exception("Not logged in")
            val email = user.email ?: throw Exception("User has no email")
            val credential = EmailAuthProvider.getCredential(email, password)
            user.reauthenticate(credential).await()
            Result.success(true)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun updateEmail(newEmail: String): Result<Boolean> {
        return try {
            val user = auth.currentUser ?: throw Exception("Not logged in")
            user.verifyBeforeUpdateEmail(newEmail).await() // Using modern API for Firebase
            Result.success(true)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    suspend fun updatePassword(newPassword: String): Result<Boolean> {
        return try {
            val user = auth.currentUser ?: throw Exception("Not logged in")
            user.updatePassword(newPassword).await()
            Result.success(true)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * Permanently deletes the account: rides, profile document and the login itself.
     * Needs the current password because Firebase requires a recent sign-in for deletion.
     */
    suspend fun deleteAccount(context: Context, password: String): Result<Unit> = runCatching {
        val user = auth.currentUser ?: throw IllegalStateException("Not logged in")
        val email = user.email ?: throw IllegalStateException("This account has no email")
        user.reauthenticate(EmailAuthProvider.getCredential(email, password)).await()

        // End any ride first so the service doesn't write a ride after the data is gone
        if (RideSession.state.value.isRecording) {
            RideTrackingService.stop(context)
            withTimeoutOrNull(3000) { RideSession.state.first { !it.isRecording } }
        }
        HelmetBleManager.getInstance(context).disconnect()

        val userDoc = firestore.collection("users").document(user.uid)
        val rides = userDoc.collection("rides").get().await().documents
        rides.chunked(400).forEach { chunk -> // Firestore batches hold at most 500 writes
            firestore.batch().apply { chunk.forEach { delete(it.reference) } }.commit().await()
        }
        userDoc.delete().await()
        user.delete().await()

        SafetySettings.clearAccountData(context)
        RecentPlaces(context).clear()
    }

    suspend fun sendPasswordResetEmail(email: String): Result<Boolean> {
        return try {
            auth.sendPasswordResetEmail(email).await()
            Result.success(true)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

}