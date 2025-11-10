<template>
  <div class="tree-node" :style="{ paddingLeft: `${depth * 20}px` }">
    <!-- Expandable node with nested fields -->
    <div v-if="hasNestedFields" class="node-line">
      <v-btn
        :icon="expanded ? 'mdi-chevron-down' : 'mdi-chevron-right'"
        size="x-small"
        variant="text"
        @click="toggleExpand"
        class="expand-btn"
      />
      <span class="field-name" :class="{ 'highlight': isHighlighted }">{{ fieldName }}</span>
      <span class="separator">:</span>
      <span class="field-type">{{ typeDisplay }}</span>
    </div>

    <!-- Leaf node (primitive type) -->
    <div v-else class="node-line leaf-node">
      <span class="indent-spacer"></span>
      <span class="field-name" :class="{ 'highlight': isHighlighted }">{{ fieldName }}</span>
      <span class="separator">:</span>
      <span class="field-type primitive">{{ typeDisplay }}</span>
    </div>

    <!-- Nested fields (when expanded) -->
    <div v-if="hasNestedFields && expanded" class="nested-fields">
      <SchemaTreeNode
        v-for="(value, key) in nestedFields"
        :key="String(key)"
        :field-name="String(key)"
        :field-value="value"
        :depth="depth + 1"
        :search="search"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

const props = defineProps<{
  fieldName: string;
  fieldValue: any;
  depth: number;
  search?: string;
}>();

const expanded = ref(false);

// Check if value is an object (for 0.5.8 format checking)
function isObject(value: any): boolean {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}

// In 0.5.8 format, each field is { type: '...', fields: {...} }
// Check if this node has nested fields
const hasNestedFields = computed(() => {
  if (!isObject(props.fieldValue)) return false;

  // Check if it has the new format with fields property
  if (props.fieldValue.fields && Object.keys(props.fieldValue.fields).length > 0) {
    return true;
  }

  return false;
});

// Get nested fields for display
const nestedFields = computed(() => {
  if (!isObject(props.fieldValue)) return {};

  // In 0.5.8 format, nested fields are in the 'fields' property
  if (props.fieldValue.fields && Object.keys(props.fieldValue.fields).length > 0) {
    return props.fieldValue.fields;
  }

  return {};
});

// Type display string
const typeDisplay = computed(() => {
  if (!isObject(props.fieldValue)) {
    return String(props.fieldValue);
  }

  // In 0.5.8 format, type is in the 'type' property
  if (props.fieldValue.type) {
    return props.fieldValue.type;
  }

  return 'Object';
});

// Check if field name matches search
const isHighlighted = computed(() => {
  if (!props.search) return false;
  return props.fieldName.toLowerCase().includes(props.search.toLowerCase());
});

function toggleExpand() {
  expanded.value = !expanded.value;
}
</script>

<style scoped lang="scss">
.tree-node {
  margin: 2px 0;
}

.node-line {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 0;
  border-radius: 4px;
  transition: background-color 0.2s;

  &:hover {
    background: rgba(var(--v-theme-primary), 0.05);
  }

  &.leaf-node {
    padding-left: 4px;
  }
}

.expand-btn {
  flex-shrink: 0;
  margin-right: 4px;
}

.indent-spacer {
  width: 28px;
  flex-shrink: 0;
}

.field-name {
  font-weight: 600;
  color: rgb(var(--v-theme-accent));
  transition: background-color 0.2s;

  &.highlight {
    background: rgba(var(--v-theme-warning), 0.3);
    padding: 0 4px;
    border-radius: 3px;
  }
}

.separator {
  color: rgb(var(--v-theme-on-surface));
  opacity: 0.5;
}

.field-type {
  color: rgb(var(--v-theme-info));
  font-style: italic;

  &.primitive {
    color: rgb(var(--v-theme-success));
    font-weight: 500;
    font-style: normal;
  }
}

.nested-fields {
  margin-left: 0;
}
</style>
