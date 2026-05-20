import { computed, ref } from 'vue'
import { isEmail } from '@/utils/validate'

type FieldErrors = {
  email: string | null
  password: string | null
}

function emptyErrors(): FieldErrors {
  return {
    email: null,
    password: null,
  }
}

export function useLoginForm() {
  const errorMessage = ref<string | null>(null)
  const email = ref('')
  const password = ref('')
  const showPassword = ref(false)

  const fieldErrors = ref<FieldErrors>(emptyErrors()) // 필드 에러용

  function validate(): boolean {
    const e = email.value.trim()
    const p = password.value.trim()

    const errs = emptyErrors()

    if (!e) {
      errs.email = '이메일을 입력해주세요.'
    } else if (!isEmail(e)) {
      errs.email = '올바른 이메일 형식이 아닙니다.'
    }

    if (!p) {
      errs.password = '비밀번호를 입력해주세요.'
    }

    fieldErrors.value = errs

    return !errs.email && !errs.password
  }

  function onInputChanged() {
    fieldErrors.value = emptyErrors()
    errorMessage.value = null
  }

  function onBlurValidate() {
    validate()
  }

  const canSubmit = computed(() => {
    const e = email.value.trim()
    const p = password.value.trim()

    if (!e) return false
    if (!isEmail(e)) return false
    if (!p) return false
    return true
  })

  async function handleSubmit(onSuccess: () => Promise<void> | void) {
    if (!canSubmit.value) return
    fieldErrors.value = emptyErrors()
    errorMessage.value = null

    if (!validate()) return

    await onSuccess()
  }

  return {
    email,
    password,
    showPassword,

    fieldErrors,
    errorMessage,

    validate,
    onInputChanged,
    onBlurValidate,

    canSubmit,
    handleSubmit,
  }
}
