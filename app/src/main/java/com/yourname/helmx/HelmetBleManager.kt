package com.yourname.helmx

import android.annotation.SuppressLint
import android.bluetooth.*
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanFilter
import android.bluetooth.le.ScanResult
import android.bluetooth.le.ScanSettings
import android.content.Context
import android.content.pm.PackageManager
import android.os.Handler
import android.os.Looper
import android.util.Log
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.update
import java.util.*

@SuppressLint("MissingPermission")
class HelmetBleManager private constructor(private val context: Context) {

    companion object {
        @Volatile
        private var INSTANCE: HelmetBleManager? = null

        fun getInstance(context: Context): HelmetBleManager {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: HelmetBleManager(context.applicationContext).also { INSTANCE = it }
            }
        }
    }

    private val bluetoothAdapter: BluetoothAdapter? by lazy {
        val bluetoothManager = context.getSystemService(Context.BLUETOOTH_SERVICE) as BluetoothManager
        bluetoothManager.adapter
    }

    // Connection state below is only modified on the main thread.
    // GATT callbacks arrive on binder threads and are posted to [handler].
    private var bluetoothGatt: BluetoothGatt? = null
    private val _helmetData = MutableStateFlow(HelmetData())
    val helmetData: StateFlow<HelmetData> = _helmetData

    private val handler = Handler(Looper.getMainLooper())
    private var isScanning = false

    // True while the user has asked to disconnect, so a drop is not treated as unexpected
    private var userInitiatedDisconnect = false

    // True once notifications were enabled in this session. Only then is a drop worth
    // auto-reconnecting; a failed first connection attempt is reported instead.
    private var hasConnected = false

    // Set when we abort a connection ourselves (e.g. wrong device), shown after the disconnect
    private var pendingErrorStatus: ConnectionStatus? = null

    private val scanTimeoutRunnable = Runnable {
        if (isScanning) {
            stopScan()
            if (bluetoothGatt == null) {
                updateStatus(ConnectionStatus.NOT_FOUND)
            }
        }
    }

    private fun updateStatus(status: ConnectionStatus) {
        _helmetData.update { it.copy(connectionStatus = status) }
    }

    // Update these UUIDs to match your Raspberry Pi BLE configuration
    // Default placeholders for custom BLE services
    private val SERVICE_UUID = UUID.fromString("0000FFE0-0000-1000-8000-00805F9B34FB")
    private val CHARACTERISTIC_UUID = UUID.fromString("0000FFE1-0000-1000-8000-00805F9B34FB")
    private val CCCD_UUID = UUID.fromString("00002902-0000-1000-8000-00805f9b34fb")

    fun isBluetoothSupported(): Boolean {
        return bluetoothAdapter != null &&
            context.packageManager.hasSystemFeature(PackageManager.FEATURE_BLUETOOTH_LE)
    }

    fun isBluetoothEnabled(): Boolean {
        return bluetoothAdapter?.isEnabled == true
    }

    fun startScan() {
        if (bluetoothAdapter == null || !bluetoothAdapter!!.isEnabled) {
            Log.e("HelmetBleManager", "Bluetooth is disabled or not available")
            return
        }

        if (isScanning || bluetoothGatt != null) return

        val scanner = bluetoothAdapter?.bluetoothLeScanner ?: return

        // Filter for "HelmX" device name as specified in project report
        val filter = ScanFilter.Builder()
            .setDeviceName("HelmX")
            .build()

        val settings = ScanSettings.Builder()
            .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY)
            .build()

        isScanning = true
        userInitiatedDisconnect = false
        hasConnected = false
        pendingErrorStatus = null
        updateStatus(ConnectionStatus.SEARCHING)
        scanner.startScan(listOf(filter), settings, scanCallback)

        // Stop scanning after 10 seconds if nothing found
        handler.removeCallbacks(scanTimeoutRunnable)
        handler.postDelayed(scanTimeoutRunnable, 10000)
    }

    fun stopScan() {
        if (!isScanning) return
        isScanning = false
        handler.removeCallbacks(scanTimeoutRunnable)
        bluetoothAdapter?.bluetoothLeScanner?.stopScan(scanCallback)
    }

    private val scanCallback = object : ScanCallback() {
        override fun onScanResult(callbackType: Int, result: ScanResult) {
            // Several results can arrive before the scan actually stops; connect only once
            if (!isScanning || bluetoothGatt != null) return
            Log.i("HelmetBleManager", "Found device: ${result.device.name} - ${result.device.address}")
            stopScan()
            connectToDevice(result.device)
        }

        override fun onScanFailed(errorCode: Int) {
            Log.e("HelmetBleManager", "Scan failed with error: $errorCode")
            isScanning = false
            handler.removeCallbacks(scanTimeoutRunnable)
            updateStatus(ConnectionStatus.SCAN_FAILED)
        }
    }

    private fun connectToDevice(device: BluetoothDevice, autoConnect: Boolean = false) {
        updateStatus(if (autoConnect) ConnectionStatus.RECONNECTING else ConnectionStatus.CONNECTING)
        bluetoothGatt = device.connectGatt(context, autoConnect, gattCallback)
        if (bluetoothGatt == null) {
            Log.e("HelmetBleManager", "connectGatt returned null")
            _helmetData.value = HelmetData(connectionStatus = ConnectionStatus.CONNECTION_FAILED)
        }
    }

    /** Abort the current connection and show [status] once the link is down. */
    private fun failConnection(gatt: BluetoothGatt, status: ConnectionStatus) {
        handler.post {
            pendingErrorStatus = status
            gatt.disconnect()
        }
    }

    private fun handleDisconnected(gatt: BluetoothGatt, status: Int) {
        Log.i("HelmetBleManager", "Disconnected from GATT server (status $status).")

        // Clear cache on disconnect to prevent stale data, then release the client.
        // Android only allows a limited number of open GATT clients.
        refreshDeviceCache(gatt)
        gatt.close()
        val isCurrent = bluetoothGatt == gatt
        if (isCurrent) bluetoothGatt = null
        // A late callback from an old connection must not override a newer scan/connection
        if (!isCurrent && (bluetoothGatt != null || isScanning)) return

        val errorStatus = pendingErrorStatus
        pendingErrorStatus = null
        when {
            userInitiatedDisconnect -> _helmetData.value = HelmetData()
            errorStatus != null -> _helmetData.value = HelmetData(connectionStatus = errorStatus)
            hasConnected && isBluetoothEnabled() -> {
                // Unexpected drop (out of range, helmet rebooted): let the stack reconnect
                // when the helmet becomes reachable again. Live values are cleared so the
                // UI does not show stale readings.
                Log.i("HelmetBleManager", "Unexpected disconnect. Waiting to reconnect...")
                _helmetData.value = HelmetData()
                connectToDevice(gatt.device, autoConnect = true)
            }
            hasConnected -> _helmetData.value = HelmetData() // Bluetooth was switched off
            else -> _helmetData.value = HelmetData(connectionStatus = ConnectionStatus.CONNECTION_FAILED)
        }
    }

    private val gattCallback = object : BluetoothGattCallback() {
        override fun onConnectionStateChange(gatt: BluetoothGatt, status: Int, newState: Int) {
            if (newState == BluetoothProfile.STATE_CONNECTED) {
                Log.i("HelmetBleManager", "Connected to GATT server. Requesting MTU...")
                // Status becomes CONNECTED only once notifications are enabled (onDescriptorWrite)

                // Request larger MTU to handle JSON strings
                if (!gatt.requestMtu(512)) gatt.discoverServices()
            } else if (newState == BluetoothProfile.STATE_DISCONNECTED) {
                handler.post { handleDisconnected(gatt, status) }
            }
        }

        override fun onMtuChanged(gatt: BluetoothGatt, mtu: Int, status: Int) {
            Log.i("HelmetBleManager", "MTU changed to $mtu, status: $status")
            // Start service discovery AFTER MTU is set
            gatt.discoverServices()
        }

        override fun onServicesDiscovered(gatt: BluetoothGatt, status: Int) {
            Log.i("HelmetBleManager", "onServicesDiscovered status: $status")
            if (status != BluetoothGatt.GATT_SUCCESS) {
                Log.e("HelmetBleManager", "Service discovery failed with status: $status")
                failConnection(gatt, ConnectionStatus.CONNECTION_FAILED)
                return
            }
            val characteristic = gatt.getService(SERVICE_UUID)?.getCharacteristic(CHARACTERISTIC_UUID)
            val descriptor = characteristic?.getDescriptor(CCCD_UUID)
            if (characteristic == null || descriptor == null) {
                Log.e("HelmetBleManager", "HelmX service/characteristic/CCCD not found on device")
                failConnection(gatt, ConnectionStatus.SERVICE_NOT_FOUND)
                return
            }

            Log.i("HelmetBleManager", "Characteristic found. Enabling notifications...")
            gatt.setCharacteristicNotification(characteristic, true)
            descriptor.value = BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE
            val descriptorResult = gatt.writeDescriptor(descriptor)
            Log.i("HelmetBleManager", "Descriptor write initiated: $descriptorResult")
            if (!descriptorResult) failConnection(gatt, ConnectionStatus.CONNECTION_FAILED)
        }

        override fun onDescriptorWrite(gatt: BluetoothGatt, descriptor: BluetoothGattDescriptor, status: Int) {
            if (descriptor.uuid != CCCD_UUID) return
            if (status == BluetoothGatt.GATT_SUCCESS) {
                Log.i("HelmetBleManager", "Notifications enabled. Helmet ready.")
                handler.post {
                    hasConnected = true
                    updateStatus(ConnectionStatus.CONNECTED)
                }
            } else {
                Log.e("HelmetBleManager", "Enabling notifications failed with status: $status")
                failConnection(gatt, ConnectionStatus.CONNECTION_FAILED)
            }
        }

        @Deprecated("Deprecated in Java")
        override fun onCharacteristicChanged(gatt: BluetoothGatt, characteristic: BluetoothGattCharacteristic) {
            handleCharacteristicChange(characteristic, characteristic.value)
        }

        override fun onCharacteristicChanged(gatt: BluetoothGatt, characteristic: BluetoothGattCharacteristic, value: ByteArray) {
            handleCharacteristicChange(characteristic, value)
        }

        private fun handleCharacteristicChange(characteristic: BluetoothGattCharacteristic, value: ByteArray?) {
            if (characteristic.uuid == CHARACTERISTIC_UUID && value != null) {
                val dataString = String(value)
                Log.d("HelmetBleManager", "Received: $dataString")
                parseHelmetData(dataString)
            }
        }
    }

    private fun parseHelmetData(rawString: String) {
        try {
            var recognised = false
            _helmetData.update { current ->
                val parsed = HelmetDataParser.parse(rawString, current)
                recognised = parsed != null
                parsed ?: current
            }
            if (!recognised) Log.w("HelmetBleManager", "Unrecognised payload: $rawString")
        } catch (e: Exception) {
            Log.e("HelmetBleManager", "Error parsing data: $rawString", e)
        }
    }

    // ---------------------------------------------------------------------------------------
    // Demo helmet (debug builds only): simulated readings for demos and screenshots when no
    // helmet is available. Never reports a crash or drowsiness.
    // ---------------------------------------------------------------------------------------

    private var demoRunnable: Runnable? = null
    private var demoTick = 0

    val isDemoMode: Boolean
        get() = demoRunnable != null

    fun startDemo() {
        if (isDemoMode || isScanning || bluetoothGatt != null) return
        demoTick = 0
        val runnable = object : Runnable {
            override fun run() {
                demoTick++
                val t = demoTick.toDouble()
                val speed = 34.0 + 8.0 * kotlin.math.sin(t / 6.0)
                _helmetData.update {
                    it.copy(
                        connectionStatus = ConnectionStatus.CONNECTED,
                        batteryLevel = (87 - demoTick / 120).coerceAtLeast(20),
                        speed = speed.toFloat(),
                        distance = (it.distance + speed / 3600.0).toFloat(),
                        temperature = (31.4 + 0.3 * kotlin.math.sin(t / 20.0)).toFloat(),
                        humidity = (58.0 + 2.0 * kotlin.math.sin(t / 25.0)).toFloat(),
                        airQuality = "Good",
                        isDrowsy = false,
                        isCrashDetected = false
                    )
                }
                handler.postDelayed(this, 1000)
            }
        }
        demoRunnable = runnable
        _helmetData.value = HelmetData(connectionStatus = ConnectionStatus.CONNECTED, distance = 3.4f)
        handler.post(runnable)
    }

    fun stopDemo() {
        demoRunnable?.let { handler.removeCallbacks(it) }
        demoRunnable = null
        _helmetData.value = HelmetData()
    }

    fun disconnect() {
        if (isDemoMode) {
            stopDemo()
            return
        }
        userInitiatedDisconnect = true
        hasConnected = false
        stopScan()
        bluetoothGatt?.let { gatt ->
            gatt.disconnect()
            refreshDeviceCache(gatt)
            gatt.close()
        }
        bluetoothGatt = null
        _helmetData.value = HelmetData()
    }

    private fun refreshDeviceCache(gatt: BluetoothGatt): Boolean {
        return try {
            val refreshMethod = gatt.javaClass.getMethod("refresh")
            val result = refreshMethod.invoke(gatt) as Boolean
            Log.d("HelmetBleManager", "GATT cache refresh result: $result")
            result
        } catch (e: Exception) {
            Log.e("HelmetBleManager", "Failed to refresh GATT cache", e)
            false
        }
    }
}
