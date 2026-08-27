<template>
  <div class="auth-modal" v-show="isVisible">
    <div class="modal-content">
      <!-- 登录表单 -->
      <div v-if="isLogin" class="form-container">
        <h2>手机号登录</h2>
        <div class="input-group">
          <span>+86</span>
          <input
            type="text"
            v-model="phone"
            placeholder="请输入手机号"
            @input="clearError"
          />
        </div>
        <div class="input-group">
          <input
            type="password"
            v-model="password"
            placeholder="请输入密码"
            @input="clearError"
          />
        </div>
        <div v-if="errorMessage" style="color: red; font-weight: bold">
          {{ errorMessage }}
        </div>
        <button
          class="auth-button"
          @click.prevent="handleLogin"
          :disabled="loading"
        >
          {{ loading ? "登录中..." : "登录" }}
        </button>

        <div class="link-prompt">
          <span class="register-link" @click="toggleAuthMode">立即注册</span>
        </div>
      </div>

      <!-- 注册表单 -->
      <div v-else class="form-container">
        <h2>手机号注册</h2>
        <div class="input-group">
          <span>+86</span>
          <input
            type="text"
            v-model="phone"
            placeholder="请输入手机号"
            @input="clearError"
          />
        </div>
        <div class="input-group">
          <input
            type="password"
            v-model="password"
            placeholder="请输入密码"
            @input="clearError"
          />
        </div>
        <div class="input-group">
          <input
            type="password"
            v-model="passwordConfirm"
            placeholder="请确认密码"
            @input="clearError"
          />
        </div>
        <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
        <button class="auth-button" @click="handleRegister" :disabled="loading">
          {{ loading ? "注册中..." : "注册" }}
        </button>

        <div class="link-prompt">
          <span class="login-link" @click="toggleAuthMode">返回登录</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ElMessage } from "element-plus";
import "element-plus/dist/index.css";
import { useAuthStore } from "@/stores/auth";
import axios from 'axios'
export default {
  data() {
    return {
      isVisible: false,
      isLogin: true,
      phone: "",
      password: "",
      passwordConfirm: "",
      errorMessage: "",
      loading: false,
      authStore: useAuthStore(),
    };
  },
  methods: {
    showModal() {
      this.isVisible = true;
      this.clearForm();
    },
    hideModal() {
      this.isVisible = false;
    },
    toggleAuthMode() {
      this.isLogin = !this.isLogin;
      this.clearForm();
    },
    clearForm() {
      this.phone = "";
      this.password = "";
      this.passwordConfirm = "";
      this.errorMessage = "";
      this.loading = false;
    },
    clearError() {
      this.errorMessage = "";
    },

    async handleLogin() {
      if (!this.validateForm("login")) return;

      this.loading = true;
      this.errorMessage = "";

      try {
       
        await this.authStore.login({
          username: this.phone,
          password: this.password,
        });
       
          this.hideModal();
          this.$emit("login-success");
          ElMessage.success("登录成功");
          // 跳转到AllFurniture页面
          this.$router.push({ name: "PersonRoom" });
       
      } catch (error) {
        this.handleLoginError(error);
      } finally {
        this.loading = false;
      }
    },

    handleLoginError(error) {
      this.loading = false;
      if (error.response && error.response.data) {
        const message =
          error.response.data.detail || "登录失败，请检查账号或密码";

        if (message.includes("No active account found")) {
          this.errorMessage = "账号未注册，请前往注册";
          // 自动跳转到注册页（可选）
          setTimeout(() => this.toggleAuthMode(), 1500);
        } else if (message.includes("Unable to log in")) {
          this.errorMessage = "密码错误，请重试";
        } else {
          this.errorMessage = message;
        }
      } else {
        this.errorMessage = "网络错误或服务无响应";
      }
    },

    async handleRegister() {
      if (!this.validateForm("register")) return;

      this.loading = true;
      this.errorMessage = "";

      try {
        const response = await axios.post("http://localhost:8000/api/auth/register/", {
          username: this.phone,
          password: this.password,
          password2: this.passwordConfirm,
        });

        if (response.status === 200 || response.status === 201) {
          this.errorMessage = "注册成功，请返回登录";
          setTimeout(() => this.toggleAuthMode(), 1500);
        } else {
          this.errorMessage = "注册失败，请重试";
        }
      } catch (error) {
        this.handleRegisterError(error);
      } finally {
        this.loading = false;
      }
    },

    handleRegisterError(error) {
      if (error.response) {
        const { data, status } = error.response;
        if (status === 400 && data.username) {
          this.errorMessage = data.username[0];
        } else if (status === 400 && data.password) {
          this.errorMessage = data.password[0];
        } else {
          this.errorMessage = "注册失败，请检查输入";
        }
      } else {
        this.errorMessage = "网络错误，请重试";
      }
    },

    validateForm(mode) {
      if (!this.phone) {
        this.errorMessage = "请输入手机号";
        return false;
      }
      if (!/^1[0-9]{10}$/.test(this.phone)) {
        this.errorMessage = "请输入有效的手机号";
        return false;
      }
      if (!this.password) {
        this.errorMessage = mode === "login" ? "请输入密码" : "请设置密码";
        return false;
      }
      if (mode === "register") {
        if (this.password.length < 6) {
          this.errorMessage = "密码长度至少为6位";
          return false;
        }
        if (!this.passwordConfirm) {
          this.errorMessage = "请确认密码";
          return false;
        }
        if (this.password !== this.passwordConfirm) {
          this.errorMessage = "两次输入的密码不一致";
          return false;
        }
      }
      return true;
    },
  },
};
</script>

<style scoped>
.auth-modal {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
}
.modal-content {
  background-color: white;
  padding: 30px;
  border-radius: 10px;
  width: 400px;
  text-align: center;
}
.input-group {
  display: flex;
  margin-bottom: 15px;
  border-bottom: 1px solid #ddd;
}
.input-group span {
  padding: 10px;
  width: 60px;
  text-align: center;
}
.input-group input {
  flex: 1;
  padding: 10px;
  border: none;
  outline: none;
  font-size: 16px;
}
.error-message {
  color: red;
  margin: 10px 0;
  text-align: left;
}
.auth-button {
  width: 100%;
  padding: 12px;
  background-color: #409eff;
  color: white;
  border: none;
  border-radius: 4px;
  margin: 20px 0;
  cursor: pointer;
}
.link-prompt {
  font-size: 14px;
  color: #666;
  margin-top: 20px;
}
.register-link,
.login-link {
  color: #409eff;
  cursor: pointer;
  text-decoration: underline;
}
</style>