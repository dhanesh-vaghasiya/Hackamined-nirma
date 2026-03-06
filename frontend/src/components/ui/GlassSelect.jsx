import * as Select from "@radix-ui/react-select";
import { ChevronDown, Check } from "lucide-react";

/**
 * Oasis-themed glass select dropdown.
 */
export default function GlassSelect({
  value,
  onValueChange,
  placeholder = "Select…",
  options = [],
}) {
  return (
    <Select.Root value={value} onValueChange={onValueChange}>
      <Select.Trigger
        className="inline-flex items-center justify-between gap-2 rounded-xl px-3.5 py-2 text-sm outline-none cursor-pointer transition-colors font-data"
        style={{
          minWidth: 160,
          background: "rgba(218,215,205,0.12)",
          border: "1px solid rgba(151,168,122,0.25)",
          color: "#FFFFFF",
          backdropFilter: "blur(12px)",
        }}
      >
        <Select.Value placeholder={placeholder} />
        <Select.Icon>
          <ChevronDown size={14} color="#97A87A" />
        </Select.Icon>
      </Select.Trigger>

      <Select.Portal>
        <Select.Content
          position="popper"
          sideOffset={6}
          className="z-[100] rounded-xl overflow-hidden shadow-xl"
          style={{
            background: "rgba(26,30,26,0.95)",
            border: "1px solid rgba(151,168,122,0.25)",
            backdropFilter: "blur(16px)",
            minWidth: "var(--radix-select-trigger-width)",
          }}
        >
          <Select.Viewport className="p-1">
            {options.map((opt) => (
              <Select.Item
                key={opt.value}
                value={opt.value}
                className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm outline-none cursor-pointer select-none transition-colors font-data"
                style={{ color: "#dad7cd" }}
                onMouseEnter={(e) =>
                  (e.currentTarget.style.background = "rgba(151,168,122,0.12)")
                }
                onMouseLeave={(e) =>
                  (e.currentTarget.style.background = "transparent")
                }
              >
                <Select.ItemIndicator>
                  <Check size={13} color="#97A87A" />
                </Select.ItemIndicator>
                <Select.ItemText>{opt.label}</Select.ItemText>
              </Select.Item>
            ))}
          </Select.Viewport>
        </Select.Content>
      </Select.Portal>
    </Select.Root>
  );
}
